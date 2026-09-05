"""Catalog routers (v1). Merchant-scoped via RLS on the pinned session + authenticated principal."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.core.exceptions import ConflictError
from api.db.models import Product, Tenant
from api.db.repositories import ProductRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.schemas.commerce import ProductIn, ProductOut
from api.services.auth import seed_demo_catalog

router = APIRouter(prefix="/v1", tags=["catalog"])


@router.get("/products", response_model=list[ProductOut])
async def list_products(session: DbSession, principal: CurrentPrincipal) -> list[ProductOut]:
    products = await ProductRepo(session).list()
    # Lazy-seed: if this tenant has no catalog yet, provision the demo products so a buyer
    # always has something to shop. Only for real tenants (skip fabricated test tenants),
    # and only when the tenant row exists to satisfy the FK.
    if not products:
        exists = await session.get(Tenant, uuid.UUID(principal.tenant_id))
        if exists is not None:
            await seed_demo_catalog(session, principal.tenant_id)
            await session.commit()
            products = await ProductRepo(session).list()
    return [ProductOut.model_validate(p) for p in products]


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
