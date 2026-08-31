"""Controllers (v1). Routers parse, authorize, call a service, return a DTO."""

from fastapi import APIRouter

from api.dependencies.auth import CurrentPrincipal
from api.schemas.common import PrincipalOut

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["ops"])
async def readyz() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/me", response_model=PrincipalOut)
async def me(principal: CurrentPrincipal) -> PrincipalOut:
    # Any authenticated principal may view its own identity; RBAC gating lives in
    # the domain routers (see require_roles / has_permission).
    return PrincipalOut(
        subject=principal.subject,
        principal_type=principal.principal_type,
        tenant_id=principal.tenant_id,
        role=principal.role,
    )
