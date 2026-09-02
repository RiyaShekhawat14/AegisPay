"""Payment DTOs. Payment only proceeds for an order with a VALID authorization (server-gated)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class PaymentCreateIn(BaseModel):
    order_id: uuid.UUID
    authorization_id: uuid.UUID


class PaymentOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    status: str
    amount_minor: int
    currency: str
    provider: str
    provider_order_id: str | None
    provider_payment_id: str | None
