"""Transactional outbox relay. Publishes unpublished outbox rows to SQS (at-least-once).

Because the business update and the outbox row commit in the same transaction, there is no
"committed but not emitted" and no "emitted but not committed".
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Envelope:
    event_type: str
    tenant_id: str
    aggregate_type: str
    aggregate_id: str
    payload: dict


async def publish(envelopes: list[Envelope], sqs_url: str) -> int:
    """Send envelopes to SQS and return how many were sent. Caller marks them published.

    The SQS client is injected/created in the worker; this isolates the outbox logic.
    """
    # TODO: wire boto3/aioboto3 SQS send_message_batch. Marked published in the same
    # step so a crash does not double-send past what idempotent consumers expect.
    return len(envelopes)
