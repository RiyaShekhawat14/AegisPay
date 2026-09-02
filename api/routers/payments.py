"""Payment routers (v1): create a payment for an authorized order, and read its status.

The money gate: a payment is only created when the order has a VALID authorization whose
amount + cart match the order. Provider timeout -> UNKNOWN (never a blind retry).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.db.repositories import OrderRepo, PaymentRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.modules.authorization.service import AuthorizationService
from api.schemas.payments import PaymentCreateIn, PaymentOut
from api.services.payments import get_provider, initiate_payment

router = APIRouter(prefix="/v1", tags=["payments"])


def _out(payment) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        order_id=payment.order_id,
        status=payment.status,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        provider=payment.provider,
        provider_order_id=payment.provider_order_id,
        provider_payment_id=payment.provider_payment_id,
    )


@router.post("/payments", response_model=PaymentOut, status_code=201)
async def create_payment(
    body: PaymentCreateIn, session: DbSession, principal: CurrentPrincipal
) -> PaymentOut:
    order = await OrderRepo(session).get(body.order_id)
    if order is None:
        raise HTTPException(404, "not found")
    authz = await AuthorizationService(session).get(body.authorization_id)
    if authz is None or authz.status != "VALID":
        raise HTTPException(403, "invalid authorization")
    if authz.cart_id != order.cart_id or authz.amount_minor != order.total_minor:
        raise HTTPException(403, "authorization does not match order")

    payment_id, _ = await initiate_payment(
        tenant_id=principal.tenant_id,
        order_id=str(order.id),
        amount_minor=order.total_minor,
        currency=order.currency,
        key=str(body.authorization_id),
        request_hash=order.cart_hash,
        provider=get_provider(),
    )
    # Re-fetch to return the persisted payment (initiate_payment commits in its own session).
    payment = await PaymentRepo(session).get(uuid.UUID(payment_id))
    if payment is None:
        raise HTTPException(500, "payment not persisted")
    return _out(payment)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal
) -> PaymentOut:
    payment = await PaymentRepo(session).get(payment_id)
    if payment is None:
        raise HTTPException(404, "not found")
    return _out(payment)
