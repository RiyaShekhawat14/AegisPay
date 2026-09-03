"""Aggregate router — include resource routers here (carts, orders, payments…)."""

from fastapi import APIRouter

from api.routers.audit import router as audit_router
from api.routers.authorizations import router as authorizations_router
from api.routers.carts import router as carts_router
from api.routers.grow import router as grow_router
from api.routers.health import router as health_router
from api.routers.orders import router as orders_router
from api.routers.passport import router as passport_router
from api.routers.payments import router as payments_router
from api.routers.products import router as products_router
from api.routers.protocol import router as protocol_router
from api.routers.reconciliation import router as reconciliation_router
from api.routers.webhooks import router as webhooks_router

router = APIRouter()
router.include_router(health_router)
router.include_router(products_router)
router.include_router(carts_router)
router.include_router(orders_router)
router.include_router(authorizations_router)
router.include_router(payments_router)
router.include_router(webhooks_router)
router.include_router(reconciliation_router)
router.include_router(audit_router)
router.include_router(passport_router)
router.include_router(grow_router)
router.include_router(protocol_router)
