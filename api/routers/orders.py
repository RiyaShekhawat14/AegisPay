"""Order routers (v1): checkout a cart into an order. Cart change invalidates checkout."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.core.exceptions import ConflictError, ValidationError
from api.db.models import Cart, Order
from api.db.repositories import CartRepo, OrderRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.modules.commerce.safety import CartLine, cart_hash
from api.schemas.commerce import OrderOut

router = APIRouter(prefix="/v1", tags=["orders"])


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal
) -> OrderOut:
    order = await OrderRepo(session).get(order_id)
    if order is None:
        raise HTTPException(404, "not found")
    return OrderOut(
        id=order.id,
        cart_id=order.cart_id,
        status=order.status,
        currency=order.currency,
        total_minor=order.total_minor,
        cart_hash=order.cart_hash,
    )


@router.post("/carts/{cart_id}/checkout", response_model=OrderOut, status_code=201)
async def checkout(cart_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal) -> OrderOut:
    cart: Cart | None = await CartRepo(session).get(cart_id)
    if cart is None:
        raise HTTPException(404, "not found")
    items = await CartRepo(session).items(cart_id)
    if not items:
        raise ValidationError("empty cart")
    lines = [
        CartLine(
            product_id=str(i.product_id),
            quantity=i.quantity,
            unit_price_minor=i.unit_price_minor,
            price_version=cart.price_version or "",
        )
        for i in items
    ]
    total = sum(i.line_total_minor for i in items)
    current_hash = cart_hash(lines)
    # A material cart change (item/price) invalidates the snapshot.
    if cart.total_minor != total or cart.cart_hash != current_hash:
        raise ConflictError("cart changed")
    order = await OrderRepo(session).add(
        Order(
            tenant_id=uuid.UUID(principal.tenant_id),
            cart_id=cart_id,
            agent_id=cart.agent_id,
            currency=cart.currency,
            total_minor=total,
            status="CREATED",
            policy_version="v1",
            cart_hash=current_hash,
            idempotency_key=str(uuid.uuid4()),
        )
    )
    return OrderOut(
        id=order.id,
        cart_id=order.cart_id,
        status=order.status,
        currency=order.currency,
        total_minor=order.total_minor,
        cart_hash=order.cart_hash,
    )
