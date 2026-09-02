"""Reconciliation: resolve UNKNOWN payments from provider truth, within a tenant.

Never blind-retry a UNKNOWN payment. Ask the provider what actually happened, then transition
to PAID or FAILED via the state machine. A legal transition is applied and counted.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.db.repositories import PaymentRepo
from api.modules.payments.state import IllegalTransition, PaymentStatus, transition

# provider reconcile() returns SUCCESS | FAILED | PENDING -> payment status
_PROVIDER_TO_STATUS = {
    "SUCCESS": PaymentStatus.PAID,
    "FAILED": PaymentStatus.FAILED,
    "PENDING": PaymentStatus.UNKNOWN,
}


async def reconcile_unknown(session: AsyncSession, provider) -> int:
    """Resolve all UNKNOWN payments in the current tenant. Returns how many were resolved."""
    repo = PaymentRepo(session)
    resolved = 0
    for payment in await repo.list_unknown():
        result = await provider.reconcile(
            order_ref=payment.provider_order_id or "", payment_ref=str(payment.id)
        )
        target = _PROVIDER_TO_STATUS.get(str(result).upper(), PaymentStatus.UNKNOWN)
        if target not in (PaymentStatus.PAID, PaymentStatus.FAILED):
            continue  # still unknown — never guess
        try:
            transition(PaymentStatus(payment.status), target)
        except IllegalTransition:
            continue  # impossible transition -> leave as-is (safe)
        payment.status = target.value
        resolved += 1
    await session.commit()
    return resolved
