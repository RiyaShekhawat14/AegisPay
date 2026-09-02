"""Webhook ingestion: verify signature before trusting the event. Webhooks are untrusted.

A rejected signature is a security event and never changes state. Applying the event to a
payment is done by the tenant-scoped reconciliation worker (cross-tenant RLS makes direct
apply unsafe here), so this boundary stays verify + ack.
"""

from __future__ import annotations


async def verify_webhook(provider, *, body: bytes, signature: str) -> bool:
    """Untrusted external event: only a valid signature is accepted."""
    return await provider.verify_webhook(body=body, signature=signature)
