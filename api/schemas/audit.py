"""Audit / passport DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    actor_type: str
    actor_id: str | None
    transaction_id: str | None
    prev_hash: str
    event_hash: str
    created_at: datetime
