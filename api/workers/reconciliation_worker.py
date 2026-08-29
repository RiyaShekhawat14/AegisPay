"""Periodic reconciliation of UNKNOWN payments (backoff, bounded attempts, escalation)."""

from api.modules.payments.provider import RazorpayAdapter
from api.modules.reconciliation.worker import reconcile


async def run_once(payment_ref: str) -> str:
    status = await reconcile(payment_ref, RazorpayAdapter())
    return status.value  # PAID | FAILED | UNKNOWN (still unknown -> escalate)
