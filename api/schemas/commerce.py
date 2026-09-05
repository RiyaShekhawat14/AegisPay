"""Commerce DTOs (API contract). Prices are server-owned; line totals are derived, never trusted.

Validation lives in Pydantic: `price_minor >= 0`, `quantity > 0` -> HTTP 422 VALIDATION_ERROR.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProductIn(BaseModel):
    sku: str
    name: str
    price_minor: int = Field(ge=0)
    category: str | None = None
    currency: str = "INR"
    image_url: str | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    sku: str
    name: str
    category: str | None
    price_minor: int
    currency: str
    status: str
    image_url: str | None = None


class CartCreateIn(BaseModel):
    agent_id: uuid.UUID


class CartItemIn(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CartItemOut(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price_minor: int
    line_total_minor: int


class CartOut(BaseModel):
    id: uuid.UUID
    status: str
    currency: str
    total_minor: int
    cart_hash: str | None
    items: list[CartItemOut]


class OrderOut(BaseModel):
    id: uuid.UUID
    cart_id: uuid.UUID
    status: str
    currency: str
    total_minor: int
    cart_hash: str
