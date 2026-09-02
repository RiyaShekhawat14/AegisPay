"""Payment service: wires the tested PurchaseFlow to the DB, Razorpay, outbox and idempotency.

Runs inside a tenant-pinned transaction. A provider timeout transitions the payment to
UNKNOWN (never a blind retry); reconciliation resolves it from provider truth.
"""

from __future__ import annotations

import uuid

from api.core.config import get_settings
from api.core.observability import record_payment
from api.db import repositories
from api.db.session import tenant_session
from api.modules.commerce.flow import MemIdem, MemOutbox, Payment, PurchaseFlow


def get_provider():
    """Real Razorpay when test keys are configured; otherwise the in-memory mock (tests/dev)."""
    from api.services.razorpay import RazorpayAdapter
    from api.services.razorpay_mock import RazorpayMock

    if get_settings().razorpay_key_id:
        return RazorpayAdapter()
    return RazorpayMock()


class DbPaymentAdapter:
    """Maps the flow's Payment object to the payments repository (tenant-pinned row)."""

    def __init__(self, session, tenant_id: str) -> None:
        self._repo = repositories.PaymentRepo(session)
        self._tenant_id = tenant_id

    async def save(self, p: Payment) -> None:
        await self._repo.add(
            repositories.Payment(
                id=uuid.UUID(p.id),
                tenant_id=uuid.UUID(self._tenant_id),
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
    provider=None,
    outbox=None,
) -> tuple[str, str]:
    """Returns (payment_id, status). Idempotent; UNKNOWN on provider timeout."""
    provider = provider or get_provider()
    outbox = outbox or MemOutbox()
    async with tenant_session(tenant_id) as session:
        flow = PurchaseFlow(
            repo=DbPaymentAdapter(session, tenant_id), idem=MemIdem(), outbox=outbox
        )
        outcome = await flow.initiate_payment(
            order_id=order_id,
            amount_minor=amount_minor,
            currency=currency,
            provider=provider,
            key=key,
            request_hash=request_hash,
        )
        record_payment(outcome.status)
        return outcome.payment_id or "", outcome.status
