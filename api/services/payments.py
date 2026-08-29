"""Payment service: wires the tested PurchaseFlow to the DB, Razorpay, outbox and idempotency.

Runs inside a tenant-pinned transaction. A provider timeout transitions the payment to
UNKNOWN (never a blind retry); reconciliation resolves it from provider truth.
"""

from __future__ import annotations

from api.core.observability import record_payment
from api.db import repositories
from api.db.session import tenant_session
from api.modules.commerce.flow import MemIdem, MemOutbox, Payment, PurchaseFlow
from api.services.razorpay import RazorpayAdapter


class DbPaymentAdapter:
    """Maps the flow's Payment object to the payments repository."""

    def __init__(self, session) -> None:
        self._repo = repositories.PaymentRepo(session)

    async def save(self, p: Payment) -> None:
        await self._repo.add(
            repositories.Payment(
                order_id=p.order_id,
                amount_minor=p.amount_minor,
                currency=p.currency,
                provider=p.provider,
                provider_order_id=p.provider_order_id,
                provider_payment_id=p.provider_payment_id,
                status=p.status,
                idempotency_key=p.order_id + p.id,
            )
        )

    async def get(self, payment_id: str):
        return await self._repo.get(payment_id)


async def initiate_payment(
    *,
    tenant_id: str,
    order_id: str,
    amount_minor: int,
    currency: str,
    key: str,
    request_hash: str,
    outbox=MemOutbox,
) -> tuple[str, str]:
    """Returns (payment_id, status). Idempotent; UNKNOWN on provider timeout."""
    async with tenant_session(tenant_id) as session:
        flow = PurchaseFlow(repo=DbPaymentAdapter(session), idem=MemIdem(), outbox=outbox)
        outcome = await flow.initiate_payment(
            order_id=order_id,
            amount_minor=amount_minor,
            currency=currency,
            provider=RazorpayAdapter(),
            key=key,
            request_hash=request_hash,
        )
        record_payment(outcome.status)
        return outcome.payment_id or "", outcome.status
