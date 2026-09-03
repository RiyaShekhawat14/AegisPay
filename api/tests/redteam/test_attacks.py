"""Red Team (Phase 15): adversarial attacks must fail safely.

Each attack below must be blocked by the guardrails — RLS, the authorization gate, schema
validation, policy deny, and the AI tool allowlist. A passed test means the attack did NOT
succeed (no unauthorized money move, no cross-tenant leak).
"""

from __future__ import annotations

import time
import uuid

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from api.core.rls import pin_tenant
from api.db.session import Session
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
            {"i": agent, "t": tenant, "n": "a", "ty": "SELL"},
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


@pytest.fixture()
async def ctx():
    from api.main import app

    tenant, agent = uuid.uuid4(), uuid.uuid4()
    await _seed(tenant, agent)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield tenant, agent, c


# --- 1. tenant spoofing / cross-tenant leak (RLS) ---
@pytest.mark.asyncio
async def test_attack_cross_tenant_read_blocked(ctx):
    tenant, _, c = ctx
    h = _h(tenant)
    await c.post(
        "/v1/products", headers=h, json={"sku": "A-1", "name": "Secret", "price_minor": 100}
    )
    # Different tenant must NOT see tenant A's product.
    other = uuid.uuid4()
    r = await c.get("/v1/products", headers=_h(other))
    assert r.status_code == 200
    assert all(p["sku"] != "A-1" for p in r.json())


# --- 2. authorization bypass: pay without a valid authorization ---
@pytest.mark.asyncio
async def test_attack_payment_without_valid_authorization(ctx):
    tenant, agent, c = ctx
    h = _h(tenant)
    pid = (
        await c.post(
            "/v1/products", headers=h, json={"sku": "B-1", "name": "Shoes", "price_minor": 5000}
        )
    ).json()["id"]
    cid = (await c.post("/v1/carts", headers=h, json={"agent_id": str(agent)})).json()["id"]
    await c.post(f"/v1/carts/{cid}/items", headers=h, json={"product_id": pid, "quantity": 1})
    order = (await c.post(f"/v1/carts/{cid}/checkout", headers=h)).json()
    # No authorization at all -> payment rejected (403).
    r = await c.post(
        "/v1/payments",
        headers=h,
        json={"order_id": order["id"], "authorization_id": str(uuid.uuid4())},
    )
    assert r.status_code == 403


# --- 3. negative / zero price rejected (schema) ---
@pytest.mark.asyncio
async def test_attack_negative_price(ctx):
    tenant, _, c = ctx
    r = await c.post(
        "/v1/products", headers=_h(tenant), json={"sku": "N-1", "name": "Bad", "price_minor": -5}
    )
    assert r.status_code == 422


# --- 4. policy hard-cap deny (money above cap) ---
@pytest.mark.asyncio
async def test_attack_amount_above_policy_cap(ctx):
    tenant, agent, c = ctx
    h = _h(tenant)
    pid = (
        await c.post(
            "/v1/products", headers=h, json={"sku": "C-1", "name": "Big", "price_minor": 6_000_000}
        )
    ).json()["id"]
    cid = (await c.post("/v1/carts", headers=h, json={"agent_id": str(agent)})).json()["id"]
    await c.post(f"/v1/carts/{cid}/items", headers=h, json={"product_id": pid, "quantity": 1})
    r = await c.post("/v1/authorizations", headers=h, json={"cart_id": str(cid)})
    assert r.status_code == 403  # POLICY_DENIED
    assert r.json()["code"] == "POLICY_DENIED"


# --- 5. AI can never move money (tool allowlist) ---
def test_attack_ai_has_no_money_tool():
    from ai_runtime.tools.registry import is_allowed, is_forbidden

    assert is_allowed("discover_products") is True
    assert is_allowed("execute_payment") is False
    assert is_allowed("capture") is False
    assert is_allowed("refund") is False
    assert is_forbidden("execute_payment") is True
