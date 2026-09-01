"""Cart routers (v1): create cart, add items, view cart. Server-owned prices + cart hashing."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.db.models import Cart, CartItem
from api.db.repositories import CartRepo, ProductRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.modules.commerce.safety import CartLine, cart_hash
from api.schemas.commerce import CartCreateIn, CartItemIn, CartItemOut, CartOut

router = APIRouter(prefix="/v1", tags=["carts"])


def _to_cart_out(cart: Cart, items: list[CartItem]) -> CartOut:
    return CartOut(
        id=cart.id,
        status=cart.status,
        currency=cart.currency,
        total_minor=cart.total_minor,
        cart_hash=cart.cart_hash,
        items=[
            CartItemOut(
                product_id=i.product_id,
                quantity=i.quantity,
                unit_price_minor=i.unit_price_minor,
                line_total_minor=i.line_total_minor,
            )
            for i in items
        ],
    )


async def _rehash(cart: Cart, items: list[CartItem]) -> None:
    lines = [
        CartLine(
            product_id=str(i.product_id),
            quantity=i.quantity,
            unit_price_minor=i.unit_price_minor,
            price_version=cart.price_version or "",
        )
        for i in items
    ]
    cart.total_minor = sum(i.line_total_minor for i in items)
    cart.cart_hash = cart_hash(lines) if lines else None


@router.post("/carts", response_model=CartOut, status_code=201)
async def create_cart(
    body: CartCreateIn, session: DbSession, principal: CurrentPrincipal
) -> CartOut:
    cart = await CartRepo(session).add(
        Cart(tenant_id=uuid.UUID(principal.tenant_id), agent_id=body.agent_id, total_minor=0)
    )
    return _to_cart_out(cart, [])


@router.get("/carts/{cart_id}", response_model=CartOut)
async def get_cart(cart_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal) -> CartOut:
    cart = await CartRepo(session).get(cart_id)
    if cart is None:
        raise HTTPException(404, "not found")
    return _to_cart_out(cart, await CartRepo(session).items(cart_id))


@router.post("/carts/{cart_id}/items", response_model=CartOut, status_code=201)
async def add_item(
    cart_id: uuid.UUID, body: CartItemIn, session: DbSession, principal: CurrentPrincipal
) -> CartOut:
    cart = await CartRepo(session).get(cart_id)
    if cart is None:
        raise HTTPException(404, "not found")
    product = await ProductRepo(session).get(body.product_id)
    if product is None:
        raise HTTPException(404, "product not found")
    # server-owned price; client can never set it
    line_total = product.price_minor * body.quantity
    await CartRepo(session).add(
        CartItem(
            tenant_id=uuid.UUID(principal.tenant_id),
            cart_id=cart_id,
            product_id=body.product_id,
            quantity=body.quantity,
            unit_price_minor=product.price_minor,
            line_total_minor=line_total,
        )
    )
    items = await CartRepo(session).items(cart_id)
    await _rehash(cart, items)
    await session.flush()
    return _to_cart_out(cart, items)
