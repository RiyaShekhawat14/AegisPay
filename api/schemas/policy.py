"""Authorization / policy DTOs. The gate runs server-side; the client only asks for it."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class EvaluateIn(BaseModel):
    amount_minor: int
    category: str = ""
    agent_daily_spent_minor: int = 0
    is_new_buyer: bool = False
    high_velocity: bool = False


class EvaluateOut(BaseModel):
    decision: str
    risk: str
    policy_version: str


class AuthzCreateIn(BaseModel):
    cart_id: uuid.UUID


class AuthzApproveIn(BaseModel):
    approver_id: uuid.UUID


class AuthzOut(BaseModel):
    id: uuid.UUID
    cart_id: uuid.UUID
    cart_hash: str
    amount_minor: int
    currency: str
    status: str
    policy_version: str
    risk: dict | None
