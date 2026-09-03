"""GROW DTOs: campaigns (capped budget) + opportunities."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CampaignIn(BaseModel):
    agent_id: uuid.UUID
    name: str
    budget_minor: int = Field(ge=0)
    discount_pct: float = 0
    margin_pct: float = 0
    duration_days: int = 0


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str
    budget_minor: int
    spent_minor: int
    discount_pct: float | None
    min_margin_pct: float | None


class ReserveIn(BaseModel):
    cost_minor: int = Field(gt=0)


class OpportunityGenerateIn(BaseModel):
    agent_id: uuid.UUID


class OpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    anchor_product: uuid.UUID | None
    target_products: list
    confidence: float | None
    status: str
