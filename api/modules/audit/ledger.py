"""Append-only, hash-chained, tamper-evident audit ledger.

Events are linked: event_hash = sha256(prev_hash || tenant || type || ts || payload).
Changing an old event breaks the chain (tamper-evident, not tamper-proof).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class AuditEvent:
    tenant_id: str
    event_type: str
    actor_type: str
    actor_id: str
    payload: dict
    prev_hash: str = ""
    event_hash: str = field(default="", init=False)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        base = f"{self.prev_hash}|{self.tenant_id}|{self.event_type}|{self.created_at}|{json.dumps(self.payload, sort_keys=True)}"
        self.event_hash = hashlib.sha256(base.encode()).hexdigest()


def link(previous: AuditEvent | None, event: AuditEvent) -> AuditEvent:
    if previous is not None:
        event.prev_hash = previous.event_hash
    event.__post_init__()
    return event
