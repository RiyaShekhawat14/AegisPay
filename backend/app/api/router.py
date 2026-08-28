"""HTTP routers (versioned). The money path is reached only after auth + tenant context."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1")


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["ops"])
async def readyz() -> dict[str, str]:
    return {"status": "ready"}
