"""Domain event envelope (CloudEvents-style). Events are also the audit records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    schema_version: str = "1.0"
    tenant_id: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
