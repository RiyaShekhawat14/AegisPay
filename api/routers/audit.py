"""Audit router (v1): list the tenant's tamper-evident audit trail."""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.schemas.audit import AuditEventOut
from api.services.audit import list_events

router = APIRouter(prefix="/v1", tags=["audit"])


@router.get("/audit/events", response_model=list[AuditEventOut])
async def audit_events(session: DbSession, principal: CurrentPrincipal) -> list[AuditEventOut]:
    return [
        AuditEventOut.model_validate(e) for e in await list_events(session, principal.tenant_id)
    ]
