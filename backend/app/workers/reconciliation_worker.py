"""Periodic reconciliation of UNKNOWN payments (backoff, bounded attempts, escalation)."""
from app.modules.reconciliation.worker import reconcile
from app.modules.payments.provider import RazorpayAdapter


async def run_once(payment_ref: str) -> str:
    status = await reconcile(payment_ref, RazorpayAdapter())
    return status.value  # PAID | FAILED | UNKNOWN (still unknown -> escalate)
