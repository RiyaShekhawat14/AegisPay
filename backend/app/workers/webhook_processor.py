"""Consumes provider webhooks from the queue and applies them idempotently."""
from app.modules.webhooks.processor import process
from app.modules.payments.provider import RazorpayAdapter


async def handle_message(body: bytes, signature: str, event_id: str) -> str:
    provider = RazorpayAdapter()
    return await process(provider, body=body, signature=signature, event_id=event_id)
