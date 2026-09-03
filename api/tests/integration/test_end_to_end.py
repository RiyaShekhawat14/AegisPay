"""End-to-end (Phase 16): the full control-plane chain, exercised in one flow.

Covers the whole SELL path: auth -> catalog -> cart -> checkout -> authorization -> payment
(mock) -> audit -> passport, plus reconciliation of an UNKNOWN payment. This is the
cross-service proof that the whole AegisPay backend works together.
"""

from __future__ import annotations

import time
import uuid

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from api.core.rls import pin_tenant
from api.db.repositories import PaymentRepo
from api.db.session import Session
from api.services.audit import append_audit, list_events, verify_chain
from api.services.payments import initiate_payment
from api.services.razorpay_mock import RazorpayMock
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


async def _seed(tenant: uuid.UUID, agent: uuid.UUID) -> None:
    async with Session() as s:
        await s.execute(
            text("insert into tenants (id, slug, name) values (:i, :s, :n)"),
            {"i": tenant, "s": f"slug-{tenant}", "n": "Tenant"},
        )
        await s.commit()
    async with Session() as s:
        await pin_tenant(s, str(tenant))
        await s.execute(
            text("insert into agents (id, tenant_id, name, type) values (:i, :t, :n, :ty)"),
            {"i": agent, "t": tenant, "n": "agent", "ty": "SELL"},
        )
        await s.commit()


def _h(tenant: uuid.UUID) -> dict[str, str]:
    t = sign(
        {
            "sub": "agent-1",
            "type": "AGENT",
            "tenant_id": str(tenant),
            "role": "member",
            "exp": int(time.time()) + 3600,
        },
        get_settings().jwt_secret,
    )
    return {"Authorization": f"Bearer {t}"}


@pytest.mark.asyncio
async def test_full_control_plane_flow():
    from api.main import app

    tenant, agent = uuid.uuid4(), uuid.uuid4()
    await _seed(tenant, agent)
    h = _h(tenant)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # 1. catalog
        pid = (
            await c.post(
                "/v1/products",
                headers=h,
                json={"sku": "E2E-1", "name": "Shoes", "price_minor": 5000},
            )
        ).json()["id"]
        # 2. cart + item + checkout (order)
        cid = (await c.post("/v1/carts", headers=h, json={"agent_id": str(agent)})).json()["id"]
        (await c.post(f"/v1/carts/{cid}/items", headers=h, json={"product_id": pid, "quantity": 2}))
        order = (await c.post(f"/v1/carts/{cid}/checkout", headers=h)).json()
        assert order["total_minor"] == 10000
        # 3. authorization (low amount -> VALID)
        authz = (await c.post("/v1/authorizations", headers=h, json={"cart_id": str(cid)})).json()
        assert authz["status"] == "VALID"
        # 4. payment (mock provider)
        pay = (
            await c.post(
                "/v1/payments",
                headers=h,
                json={"order_id": order["id"], "authorization_id": authz["id"]},
            )
        ).json()
        assert pay["provider"] == "razorpay"
        # 5. passport
        pp = (await c.get(f"/v1/passport/{pay['id']}", headers=h)).json()
        assert pp["transaction_id"] == order["id"]
        assert pp["authorization"] == "VALID"

    # 6. audit trail (append + verify chain) from a separate session
    async with Session() as s:
        await pin_tenant(s, str(tenant))
        e1 = await append_audit(
            s,
            tenant_id=str(tenant),
            event_type="order.created",
            actor_type="AGENT",
            actor_id="agent-1",
            transaction_id=order["id"],
            payload={"amount": 10000},
        )
        await append_audit(
            s,
            tenant_id=str(tenant),
            event_type="payment.captured",
            actor_type="SYSTEM",
            actor_id="",
            transaction_id=order["id"],
            payload={"status": "PAID"},
        )
        await s.commit()
    async with Session() as s:
        await pin_tenant(s, str(tenant))
        events = await list_events(s, str(tenant))
        assert verify_chain(events[::-1]) is True
    assert e1


@pytest.mark.asyncio
async def test_full_flow_reconciliation_of_unknown():
    tenant, agent = uuid.uuid4(), uuid.uuid4()
    await _seed(tenant, agent)
    # Build an order directly, then an UNKNOWN payment (timeout provider) and reconcile.
    cart, order = uuid.uuid4(), uuid.uuid4()
    async with Session() as s:
        await pin_tenant(s, str(tenant))
        await s.execute(
            text(
                "insert into carts (id, tenant_id, agent_id, total_minor) values (:i, :t, :a, 5000)"
            ),
            {"i": cart, "t": tenant, "a": agent},
        )
        await s.execute(
            text(
                "insert into orders (id, tenant_id, cart_id, agent_id, currency, total_minor, status, policy_version, cart_hash, idempotency_key) values (:i, :t, :c, :a, 'INR', 5000, 'CREATED', 'v1', 'h', :ik)"
            ),
            {"i": order, "t": tenant, "c": cart, "a": agent, "ik": str(uuid.uuid4())},
        )
        await s.commit()

    _, status = await initiate_payment(
        tenant_id=str(tenant),
        order_id=str(order),
        amount_minor=5000,
        currency="INR",
        key=str(uuid.uuid4()),
        request_hash="h",
        provider=RazorpayMock(timeout=True),
    )
    assert status == "UNKNOWN"

    from api.services.reconciliation import reconcile_unknown

    async with Session() as s:
        await pin_tenant(s, str(tenant))
        resolved = await reconcile_unknown(s, RazorpayMock(succeed=True))
        assert resolved == 1
    # No UNKNOWN payments remain for this tenant.
    async with Session() as s:
        await pin_tenant(s, str(tenant))
        assert len(await PaymentRepo(s).list_unknown()) == 0
