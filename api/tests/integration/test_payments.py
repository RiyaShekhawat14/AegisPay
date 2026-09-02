"""Payment (Phase 6): authorized order -> payment via provider; gate + timeout handling.

Builds an order + a VALID authorization (low amount -> auto-VALID), then pays. A provider
timeout must yield an UNKNOWN payment, never a blind success.
"""

from __future__ import annotations

import time
import uuid

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from api.core.rls import pin_tenant
from api.db.session import Session
from api.services.payments import initiate_payment
from api.services.razorpay_mock import RazorpayMock
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


async def _seed(tenant_id: uuid.UUID, agent_id: uuid.UUID) -> None:
    async with Session() as session:
        await session.execute(
            text("insert into tenants (id, slug, name) values (:i, :s, :n)"),
            {"i": tenant_id, "s": f"slug-{tenant_id}", "n": "Tenant"},
        )
        await session.commit()
    async with Session() as session:
        await pin_tenant(session, str(tenant_id))
        await session.execute(
            text("insert into agents (id, tenant_id, name, type) values (:i, :t, :n, :ty)"),
            {"i": agent_id, "t": tenant_id, "n": "agent", "ty": "SELL"},
        )
        await session.commit()


def _auth_headers(tenant_id: uuid.UUID) -> dict[str, str]:
    token = sign(
        {
            "sub": "agent-1",
            "type": "AGENT",
            "tenant_id": str(tenant_id),
            "role": "member",
            "exp": int(time.time()) + 3600,
        },
        get_settings().jwt_secret,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
async def setup():
    from api.main import app

    tenant, agent = uuid.uuid4(), uuid.uuid4()
    await _seed(tenant, agent)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield tenant, agent, c


async def _order_and_authz(client, tenant, agent, price_minor: int, category: str | None = None):
    """Create product -> cart -> order, then a VALID authorization for the cart. Returns (order_id, authz_id)."""
    h = _auth_headers(tenant)
    payload = {"sku": f"S-{uuid.uuid4()}", "name": "P", "price_minor": price_minor}
    if category:
        payload["category"] = category
    pid = (await client.post("/v1/products", headers=h, json=payload)).json()["id"]
    cid = (await client.post("/v1/carts", headers=h, json={"agent_id": str(agent)})).json()["id"]
    (
        await client.post(
            f"/v1/carts/{cid}/items", headers=h, json={"product_id": pid, "quantity": 1}
        )
    )
    order = (await client.post(f"/v1/carts/{cid}/checkout", headers=h)).json()
    authz = (await client.post("/v1/authorizations", headers=h, json={"cart_id": str(cid)})).json()
    return uuid.UUID(order["id"]), uuid.UUID(authz["id"])


@pytest.mark.asyncio
async def test_payment_happy_path(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    order_id, authz_id = await _order_and_authz(c, tenant, agent, 5000)
    r = await c.post(
        "/v1/payments",
        headers=h,
        json={"order_id": str(order_id), "authorization_id": str(authz_id)},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] in ("PAYMENT_PENDING", "CAPTURED", "PAID")
    assert body["provider"] == "razorpay"
    assert body["amount_minor"] == 5000
    # still fetchable
    r2 = await c.get(f"/v1/payments/{body['id']}", headers=h)
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_payment_requires_valid_authorization(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    order_id, _ = await _order_and_authz(c, tenant, agent, 5000)
    # A random / non-VALID authorization is rejected.
    r = await c.post(
        "/v1/payments",
        headers=h,
        json={"order_id": str(order_id), "authorization_id": str(uuid.uuid4())},
    )
    assert r.status_code == 403
    assert r.json()["code"] == "AUTHORIZATION_ERROR"


@pytest.mark.asyncio
async def test_payment_requires_auth(setup):
    _, _, c = setup
    r = await c.post(
        "/v1/payments", json={"order_id": str(uuid.uuid4()), "authorization_id": str(uuid.uuid4())}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_provider_timeout_becomes_unknown(setup):
    tenant, agent, c = setup
    order_id, _ = await _order_and_authz(c, tenant, agent, 5000)
    _, status = await initiate_payment(
        tenant_id=str(tenant),
        order_id=str(order_id),
        amount_minor=5000,
        currency="INR",
        key=str(uuid.uuid4()),
        request_hash="hash",
        provider=RazorpayMock(timeout=True),
    )
    assert status == "UNKNOWN"
