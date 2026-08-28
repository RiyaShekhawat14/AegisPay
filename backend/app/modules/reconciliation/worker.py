"""Reconciliation: resolve UNKNOWN payments from provider truth.

Never blindly retry a payment in UNKNOWN. Ask the provider what actually happened, then
transition to PAID or FAILED. Still unknown after bounded attempts → escalate.
"""
from __future__ import annotations

from app.modules.payments.provider import PaymentProvider
from app.modules.payments.state import PaymentStatus, transition


async def reconcile(payment_ref: str, provider: PaymentProvider) -> PaymentStatus:
    result = await provider.reconcile(order_ref="", payment_ref=payment_ref)
    status = {
        "SUCCESS": PaymentStatus.PAID,
        "FAILED": PaymentStatus.FAILED,
        "PENDING": PaymentStatus.UNKNOWN,
    }.get(result.status.upper(), PaymentStatus.UNKNOWN)
    # The caller transitions the stored payment to `status` via the state machine
    # (UNKNOWN -> PAID/FAILED is legal; blind retry is never performed here).
    return status
