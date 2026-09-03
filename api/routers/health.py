"""Controllers (v1). Routers parse, authorize, call a service, return a DTO."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from api.core.metrics import prometheus_text
from api.db.session import engine
from api.dependencies.auth import CurrentPrincipal
from api.schemas.common import PrincipalOut

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/metrics", response_class=PlainTextResponse, tags=["ops"])
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(prometheus_text())


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/live", tags=["ops"])
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["ops"])
async def readyz(request: Request) -> JSONResponse:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
    except Exception:  # noqa: BLE001 - a readiness probe must report "not ready" on ANY db failure
        return JSONResponse(
            {
                "code": "NOT_READY",
                "message": "database unreachable",
                "request_id": getattr(request.state, "request_id", ""),
                "retryable": True,
            },
            status_code=503,
        )
    return JSONResponse({"status": "ready"})


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
