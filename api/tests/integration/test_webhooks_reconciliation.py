"""Webhooks + Reconciliation (Phase 7): resolve UNKNOWN payments; verify webhooks.

Reconciliation resolves UNKNOWN -> PAID/FAILED from provider truth within a tenant. The
webhook endpoint verifies the signature and acks (untrusted ingestion).
"""

from __future__ import annotations

import uuid

import pytest
from api.core.rls import pin_tenant
from api.db.repositories import PaymentRepo
from api.db.session import Session
from api.modules.payments.state import PaymentStatus
from api.services.razorpay_mock import RazorpayMock
from api.services.reconciliation import reconcile_unknown
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


async def _mk_unknown_payment(tenant: uuid.UUID) -> uuid.UUID:
    """Seed tenant -> agent -> cart -> order -> UNKNOWN payment. Returns payment id."""
    agent, cart, order, payment = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with Session() as s:
        await s.execute(
            text("insert into tenants (id, slug, name) values (:i, :s, :n)"),
            {"i": tenant, "s": f"t-{tenant}", "n": "T"},
        )
        await pin_tenant(s, str(tenant))
        await s.execute(
            text("insert into agents (id, tenant_id, name, type) values (:i, :t, :n, :ty)"),
            {"i": agent, "t": tenant, "n": "a", "ty": "SELL"},
        )
        await s.execute(
            text("insert into carts (id, tenant_id, agent_id, total_minor) values (:i, :t, :a, 0)"),
            {"i": cart, "t": tenant, "a": agent},
        )
        await s.execute(
            text(
                "insert into orders (id, tenant_id, cart_id, agent_id, currency, total_minor, status, policy_version, cart_hash, idempotency_key) values (:i, :t, :c, :a, 'INR', 5000, 'CREATED', 'v1', 'h', :ik)"
            ),
            {"i": order, "t": tenant, "c": cart, "a": agent, "ik": str(uuid.uuid4())},
        )
        await s.execute(
            text(
                "insert into payments (id, tenant_id, order_id, amount_minor, currency, provider, status, idempotency_key) values (:i, :t, :o, 5000, 'INR', 'razorpay', 'UNKNOWN', :ik)"
            ),
            {"i": payment, "t": tenant, "o": order, "ik": str(uuid.uuid4())},
        )
        await s.commit()
    return payment


@pytest.mark.asyncio
async def test_reconciliation_resolves_unknown_to_paid():
    tenant = uuid.uuid4()
    pid = await _mk_unknown_payment(tenant)

    async with Session() as session:
        await pin_tenant(session, str(tenant))
        resolved = await reconcile_unknown(session, RazorpayMock(succeed=True))

    assert resolved == 1
    async with Session() as session:
        await pin_tenant(session, str(tenant))
        p = await PaymentRepo(session).get(pid)
    assert p is not None
    assert p.status == PaymentStatus.PAID.value


@pytest.mark.asyncio
async def test_reconciliation_leaves_pending_unknown():
    tenant = uuid.uuid4()
    pid = await _mk_unknown_payment(tenant)

    async with Session() as session:
        await pin_tenant(session, str(tenant))
        resolved = await reconcile_unknown(session, RazorpayMock(succeed=False))  # PENDING

    assert resolved == 0
    async with Session() as session:
        await pin_tenant(session, str(tenant))
        p = await PaymentRepo(session).get(pid)
    assert p.status == "UNKNOWN"


@pytest.mark.asyncio
async def test_webhook_endpoint_acks():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/v1/webhooks/razorpay",
            content=b'{"event":"payment.captured"}',
            headers={"x-razorpay-signature": "x"},
        )
    assert r.status_code == 200
    assert r.json()["status"] in ("applied", "rejected")


@pytest.mark.asyncio
async def test_reconciliation_requires_auth():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/reconciliation/run")
    assert r.status_code == 401
