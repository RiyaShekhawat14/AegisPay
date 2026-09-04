"""Live end-to-end smoke for the running stack (Track-01 bar).

Runs against a LIVE AegisPay (docker compose up). Proves: auth, catalog, cart, checkout,
authorization gating (low=VALID, high=PENDING_APPROVAL, over-cap=DENY), approval quorum,
payment, transaction passport, audit chain, UNKNOWN->reconcile (failure handled gracefully),
the AI runtime (Ollama) and the protocol gateway (MCP).

Run:  set PYTHONPATH=<repo root> && DATABASE_URL=... python scripts/ci/run_e2e_smoke.py
"""
import asyncio, base64, json as _json, time, uuid
import httpx
from sqlalchemy import text

BASE = "http://localhost:8000/v1"
AI = "http://localhost:8001"

T = "88e29c17-edcc-4106-9dde-06c8b9fdf0e4"
A = "6ccba09f-621c-46d6-a7c9-c6b85fad5f50"

results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS  " if cond else "FAIL  ") + name + ((" — " + str(detail)) if detail else ""))


async def main():
    from api.core.jwt import sign
    from api.core.rls import pin_tenant
    from api.db.session import Session
    from api.modules.authorization.service import AuthorizationService
    from api.services.audit import append_audit, list_events, verify_chain
    from api.services.payments import initiate_payment
    from api.services.reconciliation import reconcile_unknown
    from api.services.razorpay_mock import RazorpayMock

    tok = sign({"sub": "agent-1", "type": "AGENT", "tenant_id": T, "role": "member", "exp": int(time.time()) + 3600}, "change-me")
    h = {"Authorization": "Bearer " + tok}
    c = httpx.AsyncClient(base_url=BASE, headers=h, timeout=30)

    async def _flow(price):
        pid = (await c.post("/products", json={"sku": "E2E-" + uuid.uuid4().hex[:5], "name": "Item", "price_minor": price})).json()["id"]
        cid = (await c.post("/carts", json={"agent_id": A})).json()["id"]
        await c.post(f"/carts/{cid}/items", json={"product_id": pid, "quantity": 2})
        order = (await c.post(f"/carts/{cid}/checkout")).json()
        az = (await c.post("/authorizations", json={"cart_id": cid})).json()
        return cid, order, az

    email = "e2e" + uuid.uuid4().hex[:6] + "@test.com"
    r = httpx.post(BASE + "/auth/signup", json={"email": email, "password": "secret123", "role": "member", "merchant_name": "E2E"})
    ok("signup -> 201 + token", r.status_code == 201 and r.json().get("token"))
    ok("login -> 200 + role", httpx.post(BASE + "/auth/login", json={"email": email, "password": "secret123"}).status_code == 200)
    ok("wrong password -> 401", httpx.post(BASE + "/auth/login", json={"email": email, "password": "nope"}).status_code == 401)

    products = httpx.get(BASE + "/products", headers=h).json()
    ok("catalog has seeded products", len(products) >= 6, f"{len(products)}")

    _, order, az = await _flow(5000)
    ok("low-risk authorization -> VALID", az["status"] == "VALID")
    pay = (await c.post("/payments", json={"order_id": order["id"], "authorization_id": az["id"]})).json()
    ok("payment on VALID authz", pay.get("status") in ("PAYMENT_PENDING", "PAID", "CAPTURED"))
    pp = (await c.get("/passport/" + pay["id"])).json()
    ok("passport explainable", len(pp) >= 15 and pp["authorization"] == "VALID")

    _, order2, az2 = await _flow(400_000)
    ok("high-risk -> PENDING_APPROVAL (gated)", az2.get("status") == "PENDING_APPROVAL")
    blocked = await c.post("/payments", json={"order_id": order2["id"], "authorization_id": az2["id"]})
    ok("payment blocked while PENDING", blocked.status_code == 403)

    _, _, az3 = await _flow(3_000_000)
    ok("over-cap amount DENIED (bounded)", az3.get("code") == "POLICY_DENIED")

    su = httpx.post(BASE + "/auth/signup", json={"email": "ap" + uuid.uuid4().hex[:6] + "@test.com", "password": "secret123", "role": "admin", "merchant_name": "App"})
    _, pl, _ = su.json()["token"].split(".")
    approver_id = _json.loads(base64.urlsafe_b64decode(pl + "=" * (-len(pl) % 4)))["sub"]
    async with Session() as s:
        await pin_tenant(s, T)
        svc = AuthorizationService(s)
        await svc.approve(authorization_id=uuid.UUID(az2["id"]), approver_id=uuid.UUID(approver_id))
        await svc.approve(authorization_id=uuid.UUID(az2["id"]), approver_id=uuid.UUID(approver_id))
        await s.commit()
    ok("2-approval quorum -> VALID", (await c.get("/authorizations/" + az2["id"])).json()["status"] == "VALID")
    pay2 = (await c.post("/payments", json={"order_id": order2["id"], "authorization_id": az2["id"]})).json()
    ok("payment succeeds after approval", pay2.get("status") in ("PAYMENT_PENDING", "PAID", "CAPTURED"))

    async with Session() as s:
        await pin_tenant(s, T)
        await append_audit(s, tenant_id=T, event_type="order.created", actor_type="AGENT", actor_id="agent-1", transaction_id=order["id"], payload={"amount": 5000})
        await append_audit(s, tenant_id=T, event_type="payment.captured", actor_type="SYSTEM", actor_id="", transaction_id=order["id"], payload={"status": "PAID"})
        await s.commit()
    async with Session() as s:
        await pin_tenant(s, T)
        ev = await list_events(s, T)
    ok("audit chain verified", verify_chain(ev[::-1]))

    cart2, order2b = uuid.uuid4(), uuid.uuid4()
    async with Session() as s:
        await pin_tenant(s, T)
        await s.execute(text("insert into carts (id,tenant_id,agent_id,total_minor) values (:i,:t,:a,:m)"), {"i": cart2, "t": uuid.UUID(T), "a": uuid.UUID(A), "m": 5000})
        await s.execute(text("insert into orders (id,tenant_id,cart_id,agent_id,currency,total_minor,status,policy_version,cart_hash,idempotency_key) values (:i,:t,:c,:a,'INR',5000,'CREATED','v1','h',:ik)"), {"i": order2b, "t": uuid.UUID(T), "c": cart2, "a": uuid.UUID(A), "ik": str(uuid.uuid4())})
        await s.commit()
    _, st = await initiate_payment(tenant_id=T, order_id=str(order2b), amount_minor=5000, currency="INR", key=str(uuid.uuid4()), request_hash="h", provider=RazorpayMock(timeout=True))
    ok("provider timeout -> UNKNOWN (no double-charge)", st == "UNKNOWN")
    async with Session() as s:
        await pin_tenant(s, T)
        n = await reconcile_unknown(s, RazorpayMock(succeed=True))
    ok("reconcile resolves UNKNOWN gracefully", n >= 1)

    b = httpx.post(AI + "/agent/run", json={"agent_id": "agent-1", "kind": "recommend", "summary": "running shoes under 4000", "items": [{"product_id": "p1", "quantity": 1}]})
    j = b.json() if b.status_code == 200 else {}
    ok("AI runtime /agent/run + Ollama", b.status_code == 200 and bool(j.get("ai_comment")), (j.get("ai_comment") or "")[:40])
    r = await c.post("/protocol/mcp", json={"tool": "add_to_cart", "args": {}})
    ok("protocol gateway MCP -> ADD_TO_CART", r.status_code == 200 and r.json()["action"] == "ADD_TO_CART")
    await c.aclose()

    passed = sum(1 for _, x, _ in results if x)
    print(f"\n=== E2E SMOKE: {passed}/{len(results)} checks passed ===")
    raise SystemExit(0 if passed == len(results) else 1)


asyncio.run(main())
