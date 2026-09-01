"""Aggregate router — include resource routers here (carts, orders, payments…)."""

from fastapi import APIRouter

from api.routers.carts import router as carts_router
from api.routers.health import router as health_router
from api.routers.orders import router as orders_router
from api.routers.products import router as products_router

router = APIRouter()
router.include_router(health_router)
router.include_router(products_router)
router.include_router(carts_router)
router.include_router(orders_router)
