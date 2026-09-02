"""Reconciliation router (v1). Admin/operator action scoped to the authenticated tenant."""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.services.payments import get_provider
from api.services.reconciliation import reconcile_unknown

router = APIRouter(prefix="/v1", tags=["reconciliation"])


@router.post("/reconciliation/run")
async def run_reconciliation(session: DbSession, principal: CurrentPrincipal) -> dict[str, int]:
    resolved = await reconcile_unknown(session, get_provider())
    return {"resolved": resolved}
