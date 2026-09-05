"""Catalog routers (v1). Merchant-scoped via RLS on the pinned session + authenticated principal."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.core.exceptions import ConflictError
from api.db.models import Product
from api.db.repositories import ProductRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.schemas.commerce import ProductIn, ProductOut

router = APIRouter(prefix="/v1", tags=["catalog"])


@router.get("/products", response_model=list[ProductOut])
async def list_products(session: DbSession, principal: CurrentPrincipal) -> list[ProductOut]:
    return [ProductOut.model_validate(p) for p in await ProductRepo(session).list()]


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal
) -> ProductOut:
    product = await ProductRepo(session).get(product_id)
    if product is None:
        raise HTTPException(404, "not found")
    return ProductOut.model_validate(product)


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductIn, session: DbSession, principal: CurrentPrincipal
) -> ProductOut:
    if await ProductRepo(session).by_sku(body.sku) is not None:
        raise ConflictError("sku already exists")
    product = await ProductRepo(session).add(
        Product(
            tenant_id=uuid.UUID(principal.tenant_id),
            sku=body.sku,
            name=body.name,
            category=body.category,
            price_minor=body.price_minor,
            currency=body.currency,
            image_url=body.image_url,
        )
    )
    return ProductOut.model_validate(product)
