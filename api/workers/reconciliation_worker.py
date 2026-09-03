"""Periodic reconciliation of UNKNOWN payments (backoff, bounded attempts, escalation).

`reconcile_all` is the cross-tenant worker loop: for every tenant it pins the RLS context and
resolves that tenant's UNKNOWN payments from provider truth. Workers are idempotent.
"""

from __future__ import annotations

from sqlalchemy import select

from api.db.models import Tenant
from api.db.session import Session, tenant_session
from api.services.payments import get_provider
from api.services.reconciliation import reconcile_unknown


async def run_once(payment_ref: str) -> str:
    from api.modules.payments.provider import RazorpayAdapter
    from api.modules.reconciliation.worker import reconcile

    status = await reconcile(payment_ref, RazorpayAdapter())
    return status.value  # PAID | FAILED | UNKNOWN (still unknown -> escalate)


async def reconcile_all(provider=None) -> int:
    """Resolve every tenant's UNKNOWN payments. Returns how many were resolved."""
    provider = provider or get_provider()
    async with Session() as master:
        # tenants has no RLS, so the worker can enumerate them without a tenant context.
        tenant_ids = list((await master.execute(select(Tenant.id))).scalars().all())
    resolved = 0
    for tenant_id in tenant_ids:
        async with tenant_session(str(tenant_id)) as session:
            resolved += await reconcile_unknown(session, provider)
    return resolved
