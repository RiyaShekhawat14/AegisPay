"""Authorization gate (Phase 5): policy/risk/evaluate + create/approve with quorum.

A cart is built (product + agent), then authorized. Low amount -> VALID immediately;
high amount -> PENDING_APPROVAL and only becomes VALID after the required approvals.
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


async def _approvers(count: int) -> list[uuid.UUID]:
    """Create `count` users (approvals.approver_id FKs to users)."""
    ids: list[uuid.UUID] = []
    async with Session() as session:
        for i in range(count):
            uid = uuid.uuid4()
            await session.execute(
                text("insert into users (id, email, password_hash) values (:i, :e, :p)"),
                {"i": uid, "e": f"u{i}-{uid}@x.com", "p": "hash"},
            )
            ids.append(uid)
        await session.commit()
    return ids


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


async def _cart(client, tenant, agent, price_minor: int, category: str | None = None) -> uuid.UUID:
    h = _auth_headers(tenant)
    payload = {"sku": f"S-{uuid.uuid4()}", "name": "P", "price_minor": price_minor}
    if category:
        payload["category"] = category
    r = await client.post("/v1/products", headers=h, json=payload)
    pid = r.json()["id"]
    r = await client.post("/v1/carts", headers=h, json={"agent_id": str(agent)})
    cid = r.json()["id"]
    r = await client.post(
        f"/v1/carts/{cid}/items", headers=h, json={"product_id": pid, "quantity": 1}
    )
    assert r.json()["total_minor"] == price_minor
    return cid


@pytest.mark.asyncio
async def test_evaluate_low_and_high(setup):
    tenant, _, c = setup
    h = _auth_headers(tenant)
    r = await c.post("/v1/policy/evaluate", headers=h, json={"amount_minor": 5000})
    assert r.status_code == 200
    assert r.json()["decision"] == "ALLOW"
    assert r.json()["risk"] == "LOW"

    r = await c.post("/v1/policy/evaluate", headers=h, json={"amount_minor": 500_000})
    assert r.json()["decision"] == "HUMAN_APPROVAL_REQUIRED"
    assert r.json()["risk"] == "HIGH"


@pytest.mark.asyncio
async def test_low_amount_authorizes_immediately(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    cart_id = await _cart(c, tenant, agent, 5000)
    r = await c.post("/v1/authorizations", headers=h, json={"cart_id": str(cart_id)})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "VALID"


@pytest.mark.asyncio
async def test_high_amount_requires_quorum(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    cart_id = await _cart(c, tenant, agent, 500_000)
    r = await c.post("/v1/authorizations", headers=h, json={"cart_id": str(cart_id)})
    assert r.status_code == 201, r.text
    authz_id = r.json()["id"]
    assert r.json()["status"] == "PENDING_APPROVAL"

    approvers = await _approvers(2)
    # One approval is not enough for HIGH risk (needs 2).
    r = await c.post(
        f"/v1/authorizations/{authz_id}/approve", headers=h, json={"approver_id": str(approvers[0])}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "PENDING_APPROVAL"

    # Second approval -> VALID.
    r = await c.post(
        f"/v1/authorizations/{authz_id}/approve", headers=h, json={"approver_id": str(approvers[1])}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "VALID"


@pytest.mark.asyncio
async def test_blocked_category_is_denied_via_evaluate(setup):
    tenant, _, c = setup
    r = await c.post(
        "/v1/policy/evaluate",
        headers=_auth_headers(tenant),
        json={"amount_minor": 5000, "category": "weapons"},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


@pytest.mark.asyncio
async def test_over_cap_amount_is_denied(setup):
    tenant, agent, c = setup
    h = _auth_headers(tenant)
    cart_id = await _cart(c, tenant, agent, 6_000_000)  # above 5,000,000 cap
    r = await c.post("/v1/authorizations", headers=h, json={"cart_id": str(cart_id)})
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "POLICY_DENIED"


@pytest.mark.asyncio
async def test_create_requires_auth(setup):
    _, _, c = setup
    r = await c.post("/v1/authorizations", json={"cart_id": str(uuid.uuid4())})
    assert r.status_code == 401
