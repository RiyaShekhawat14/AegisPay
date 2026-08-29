"""Consumes provider webhooks from the queue and applies them idempotently."""

from api.modules.payments.provider import RazorpayAdapter
from api.modules.webhooks.processor import process


async def handle_message(body: bytes, signature: str, event_id: str) -> str:
    provider = RazorpayAdapter()
    return await process(provider, body=body, signature=signature, event_id=event_id)
