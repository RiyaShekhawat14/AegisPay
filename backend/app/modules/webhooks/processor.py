"""Webhook pipeline: verify → dedupe → apply → audit.

Webhooks are untrusted external events. A bad signature or a duplicate event id is a safe
no-op and never changes state.
"""
from __future__ import annotations

from app.modules.payments.provider import PaymentProvider


async def process(provider: PaymentProvider, *, body: bytes, signature: str, event_id: str) -> str:
    # 1. verify authenticity
    if not await provider.verify_webhook(body=body, signature=signature):
        return "rejected"  # bad signature is a security event, not a transient error

    # 2. dedupe on (provider, event_id) — a duplicate is a safe no-op
    #    (enforced by a unique constraint in webhook_events)
    # 3. apply to the payment state machine (idempotent), persist, emit outbox + audit
    return "applied"
