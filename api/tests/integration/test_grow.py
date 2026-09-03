"""GROW (Phase 10): capped campaigns + opportunities, tenant-scoped."""

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
async def setup():
    from api.main import app

    tenant, agent = uuid.uuid4(), uuid.uuid4()
    await _seed(tenant, agent)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield tenant, agent, c


@pytest.mark.asyncio
async def test_create_campaign_and_reserve_never_overspends(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    r = await c.post(
        "/v1/campaigns",
        headers=h,
        json={
            "agent_id": str(agent),
            "name": "Launch",
            "budget_minor": 1000,
            "margin_pct": 20,
            "duration_days": 7,
        },
    )
    assert r.status_code == 201, r.text
    campaign_id = r.json()["id"]

    r = await c.post(f"/v1/campaigns/{campaign_id}/reserve", headers=h, json={"cost_minor": 600})
    assert r.status_code == 200 and r.json()["reserved"] is True
    r = await c.post(f"/v1/campaigns/{campaign_id}/reserve", headers=h, json={"cost_minor": 600})
    assert r.status_code == 409  # would overspend -> budget guard
    assert r.json()["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_campaign_caps_reject_bad_discount(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    r = await c.post(
        "/v1/campaigns",
        headers=h,
        json={"agent_id": str(agent), "name": "Big", "budget_minor": 1000, "discount_pct": 90},
    )
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_opportunities_generate_and_list(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    r = await c.post(
        "/v1/products", headers=h, json={"sku": "S-1", "name": "Shoes", "price_minor": 2000}
    )
    product_id = r.json()["id"]

    r = await c.post("/v1/opportunities/generate", headers=h, json={"agent_id": str(agent)})
    assert r.status_code == 201, r.text
    assert any(o["anchor_product"] == product_id for o in r.json())

    r = await c.get("/v1/opportunities", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_grow_requires_auth(setup):
    _, _, c = setup
    r = await c.get("/v1/opportunities")
    assert r.status_code == 401
