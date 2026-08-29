"""Aggregate router — include resource routers here (carts, orders, payments…)."""

from fastapi import APIRouter

from api.routers.health import router as health_router

router = APIRouter()
router.include_router(health_router)
