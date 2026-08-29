"""Resolves UNKNOWN payments from provider truth (never a blind retry)."""
from api.modules.reconciliation.worker import reconcile

_provider = None  # injected RazorpayAdapter


async def run(payment_ref: str) -> str:
    return await reconcile(payment_ref, _provider)
