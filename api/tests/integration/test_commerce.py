"""Catalog + commerce (Phase 4): products, carts, orders, tenant-scoped via RLS + auth.

Exercised in-process (ASGITransport). A tenant + agent are seeded in the DB; requests carry a
signed JWT (tenant_id from the token) so the middleware pins the tenant and RLS scopes rows.
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
async def ctx():
    from api.main import app

    tenant, agent = uuid.uuid4(), uuid.uuid4()
    await _seed(tenant, agent)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield tenant, agent, c


@pytest.mark.asyncio
async def test_product_cart_order_flow(ctx):
    tenant, agent, c = ctx
    h = _auth_headers(tenant)

    # create product
    r = await c.post(
        "/v1/products", headers=h, json={"sku": "SKU-1", "name": "Shoes", "price_minor": 2000}
    )
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]
    assert r.json()["tenant_id"] == str(tenant)

    # create cart
    r = await c.post("/v1/carts", headers=h, json={"agent_id": str(agent)})
    assert r.status_code == 201, r.text
    cart_id = r.json()["id"]

    # add item (qty 2) -> server price 2000 * 2 = 4000
    r = await c.post(
        f"/v1/carts/{cart_id}/items", headers=h, json={"product_id": product_id, "quantity": 2}
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_minor"] == 4000
    assert body["cart_hash"]
    assert body["items"][0]["unit_price_minor"] == 2000

    # checkout -> order
    r = await c.post(f"/v1/carts/{cart_id}/checkout", headers=h)
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["total_minor"] == 4000
    assert order["cart_hash"] == body["cart_hash"]

    # get order
    r = await c.get(f"/v1/orders/{order['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["total_minor"] == 4000

    # list products (tenant-scoped)
    r = await c.get("/v1/products", headers=h)
    assert r.status_code == 200
    assert any(p["sku"] == "SKU-1" for p in r.json())


@pytest.mark.asyncio
async def test_products_are_not_visible_across_tenants(ctx):
    tenant, _, c = ctx
    h = _auth_headers(tenant)
    r = await c.post(
        "/v1/products", headers=h, json={"sku": "SKU-A", "name": "A", "price_minor": 100}
    )
    assert r.status_code == 201

    # A different tenant's products are not listed (RLS).
    other_tenant = uuid.uuid4()
    r = await c.get("/v1/products", headers=_auth_headers(other_tenant))
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_cart_endpoints_require_auth(ctx):
    _, _, c = ctx
    r = await c.get("/v1/products")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_negative_price_rejected_as_validation_error(ctx):
    tenant, _, c = ctx
    r = await c.post(
        "/v1/products",
        headers=_auth_headers(tenant),
        json={"sku": "S", "name": "S", "price_minor": -5},
    )
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_duplicate_sku_is_conflict(ctx):
    tenant, _, c = ctx
    h = _auth_headers(tenant)
    payload = {"sku": "SKU-X", "name": "X", "price_minor": 100}
    assert (await c.post("/v1/products", headers=h, json=payload)).status_code == 201
    r = await c.post("/v1/products", headers=h, json=payload)
    assert r.status_code == 409
    assert r.json()["code"] == "CONFLICT"
