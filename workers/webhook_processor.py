"""Consumes provider webhook events from SQS and applies them idempotently."""
from api.modules.webhooks.processor import process

_provider = None  # injected RazorpayAdapter


async def handle(body: bytes, signature: str, event_id: str) -> str:
    return await process(_provider, body=body, signature=signature, event_id=event_id)
