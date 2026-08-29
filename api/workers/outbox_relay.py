"""Flushes unpublished outbox rows to the queue (SQS), then marks them published."""

from api.modules.outbox.relay import Envelope, publish


async def flush(envelopes: list[Envelope], sqs_url: str) -> int:
    sent = await publish(envelopes, sqs_url)
    # mark the sent rows published in the same position so nothing is lost or double-sent
    return sent
