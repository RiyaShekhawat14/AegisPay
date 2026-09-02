"""Audit ledger + Transaction Passport (Phase 8): tamper-evident trail + verifiable receipt.

Appends audit events, verifies the hash chain (and detects tampering), and builds a passport
from the order/payment/authorization trail.
"""

from __future__ import annotations

import time
import uuid

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from api.core.rls import pin_tenant
from api.db.session import Session
from api.services.audit import append_audit, list_events, verify_chain
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


async def _seed(tenant_id: uuid.UUID) -> None:
    async with Session() as session:
        await session.execute(
            text("insert into tenants (id, slug, name) values (:i, :s, :n)"),
            {"i": tenant_id, "s": f"slug-{tenant_id}", "n": "Tenant"},
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


@pytest.mark.asyncio
async def test_audit_events_and_chain_verify():
    tenant = uuid.uuid4()
    await _seed(tenant)
    async with Session() as session:
        await pin_tenant(session, str(tenant))
        await append_audit(
            session,
            tenant_id=str(tenant),
            event_type="order.created",
            actor_type="AGENT",
            actor_id="a1",
            payload={"amount": 5000},
        )
        await append_audit(
            session,
            tenant_id=str(tenant),
            event_type="payment.captured",
            actor_type="SYSTEM",
            actor_id="",
            payload={"status": "PAID"},
        )
        await session.commit()

    async with Session() as session:
        await pin_tenant(session, str(tenant))
        events = await list_events(session, str(tenant))
        assert len(events) == 2
        assert verify_chain(events[::-1]) is True  # verify in ASC chain order


@pytest.mark.asyncio
async def test_audit_chain_detects_tampering():
    tenant = uuid.uuid4()
    await _seed(tenant)
    async with Session() as session:
        await pin_tenant(session, str(tenant))
        await append_audit(
            session,
            tenant_id=str(tenant),
            event_type="order.created",
            actor_type="AGENT",
            actor_id="a1",
            payload={"amount": 5000},
        )
        await append_audit(
            session,
            tenant_id=str(tenant),
            event_type="payment.captured",
            actor_type="SYSTEM",
            actor_id="",
            payload={"status": "PAID"},
        )
        await session.commit()

    async with Session() as session:
        await pin_tenant(session, str(tenant))
        events = list(await list_events(session, str(tenant)))
    # Tamper with the PAYLOAD of the newest event (recompute the stored hash manually).
    tampered = list(events[::-1])
    tampered[-1].payload = {"status": "HACKED"}
    assert verify_chain(tampered) is False


@pytest.mark.asyncio
async def test_audit_events_endpoint_and_requires_auth():
    from api.main import app

    tenant = uuid.uuid4()
    await _seed(tenant)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/audit/events")
        assert r.status_code == 401
        r = await c.get("/v1/audit/events", headers=_auth_headers(tenant))
        assert r.status_code == 200
        assert r.json() == []


@pytest.mark.asyncio
async def test_passport_requires_auth_and_404_for_missing_payment():
    from api.main import app

    tenant = uuid.uuid4()
    await _seed(tenant)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/passport/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 401
        r = await c.get(
            "/v1/passport/00000000-0000-0000-0000-000000000000", headers=_auth_headers(tenant)
        )
        assert r.status_code == 404
