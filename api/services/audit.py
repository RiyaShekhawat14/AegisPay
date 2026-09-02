"""Audit service: append tamper-evident events, list them, and verify the hash chain.

Appending and verifying both use the same pure `ledger.AuditEvent` hash, so a change to any
event makes the chain break (tamper-evident). Reuses the tested ledger module.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import AuditEvent as AuditRow
from api.modules.audit.ledger import AuditEvent as LedgerEvent


async def append_audit(
    session: AsyncSession,
    *,
    tenant_id: str,
    event_type: str,
    actor_type: str,
    actor_id: str = "",
    transaction_id: str = "",
    correlation_id: str = "",
    payload: dict | None = None,
) -> str:
    prev_hash = ""
    prev = (
        (
            await session.execute(
                select(AuditRow)
                .where(AuditRow.tenant_id == uuid.UUID(tenant_id))
                .order_by(AuditRow.id.desc())
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
    if prev is not None:
        prev_hash = prev.event_hash

    event = LedgerEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        payload=payload or {},
        prev_hash=prev_hash,
    )
    row = AuditRow(
        tenant_id=uuid.UUID(tenant_id),
        event_type=event.event_type,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        transaction_id=transaction_id,
        correlation_id=correlation_id,
        payload=event.payload,
        prev_hash=event.prev_hash,
        event_hash=event.event_hash,
        created_at=datetime.fromisoformat(event.created_at),
    )
    session.add(row)
    await session.flush()
    return event.event_hash


async def list_events(session: AsyncSession, tenant_id: str) -> list[AuditRow]:
    res = await session.execute(
        select(AuditRow)
        .where(AuditRow.tenant_id == uuid.UUID(tenant_id))
        .order_by(AuditRow.id.desc())
        .limit(100)
    )
    return list(res.scalars().all())


def verify_chain(events: list) -> bool:
    """True if every event's stored hash matches a recompute and prev links are intact."""
    prev = ""
    for ev in events:
        recomputed = LedgerEvent(
            tenant_id=ev.tenant_id,
            event_type=ev.event_type,
            actor_type=ev.actor_type,
            actor_id=ev.actor_id or "",
            payload=ev.payload or {},
            prev_hash=prev,
            created_at=ev.created_at.isoformat(),
        )
        if ev.prev_hash != prev:  # a link in the chain was broken
            return False
        if ev.event_hash != recomputed.event_hash:  # an event was modified
            return False
        prev = ev.event_hash
    return True
