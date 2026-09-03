"""Workers (Phase 14): cross-tenant reconciliation resolves UNKNOWN payments per tenant."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from api.core.rls import pin_tenant
from api.db.repositories import PaymentRepo
from api.db.session import Session
from api.services.razorpay_mock import RazorpayMock
from api.services.reconciliation import reconcile_unknown


async def _mk_unknown(tenant: uuid.UUID) -> uuid.UUID:
    agent, cart, order, payment = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with Session() as s:
        await s.execute(text("insert into tenants (id, slug, name) values (:i, :s, :n)"), {"i": tenant, "s": f"t-{tenant}", "n": "T"})
        await pin_tenant(s, str(tenant))
        await s.execute(text("insert into agents (id, tenant_id, name, type) values (:i, :t, :n, :ty)"), {"i": agent, "t": tenant, "n": "a", "ty": "SELL"})
        await s.execute(text("insert into carts (id, tenant_id, agent_id, total_minor) values (:i, :t, :a, 0)"), {"i": cart, "t": tenant, "a": agent})
        await s.execute(
            text("insert into orders (id, tenant_id, cart_id, agent_id, currency, total_minor, status, policy_version, cart_hash, idempotency_key) values (:i, :t, :c, :a, 'INR', 5000, 'CREATED', 'v1', 'h', :ik)"),
            {"i": order, "t": tenant, "c": cart, "a": agent, "ik": str(uuid.uuid4())},
        )
        await s.execute(
            text("insert into payments (id, tenant_id, order_id, amount_minor, currency, provider, status, idempotency_key) values (:i, :t, :o, 5000, 'INR', 'razorpay', 'UNKNOWN', :ik)"),
            {"i": payment, "t": tenant, "o": order, "ik": str(uuid.uuid4())},
        )
        await s.commit()
    return payment


@pytest.mark.asyncio
async def test_cross_tenant_reconcile_resolves_each_tenant():
    # Each tenant's UNKNOWN payment is resolved from its own RLS scope.
    for _ in range(2):
        tenant = uuid.uuid4()
        payment_id = await _mk_unknown(tenant)
        async with Session() as session:
            await pin_tenant(session, str(tenant))
            resolved = await reconcile_unknown(session, RazorpayMock(succeed=True))
        assert resolved == 1
        async with Session() as session:
            await pin_tenant(session, str(tenant))
            p = await PaymentRepo(session).get(payment_id)
        assert p.status == "PAID"
