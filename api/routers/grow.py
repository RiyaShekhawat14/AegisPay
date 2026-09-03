"""GROW routers (v1): campaigns + opportunities, tenant-scoped."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.core.exceptions import ConflictError
from api.db.models import Campaign
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.schemas.grow import (
    CampaignIn,
    CampaignOut,
    OpportunityGenerateIn,
    OpportunityOut,
    ReserveIn,
)
from api.services.campaigns import create_campaign, reserve_budget
from api.services.opportunities import generate_opportunities, list_opportunities

router = APIRouter(prefix="/v1", tags=["grow"])


def _campaign_out(c: Campaign) -> CampaignOut:
    return CampaignOut.model_validate(c)


@router.post("/campaigns", response_model=CampaignOut, status_code=201)
async def create_campaign_route(
    body: CampaignIn, session: DbSession, principal: CurrentPrincipal
) -> CampaignOut:
    c = await create_campaign(
        session,
        tenant_id=uuid.UUID(principal.tenant_id),
        agent_id=body.agent_id,
        name=body.name,
        budget_minor=body.budget_minor,
        discount_pct=body.discount_pct,
        margin_pct=body.margin_pct,
        duration_days=body.duration_days,
    )
    return _campaign_out(c)


@router.post("/campaigns/{campaign_id}/reserve")
async def reserve_budget_route(
    campaign_id: uuid.UUID, body: ReserveIn, session: DbSession, principal: CurrentPrincipal
) -> dict[str, bool]:
    if not await reserve_budget(session, campaign_id, body.cost_minor):
        raise ConflictError("budget exceeded")
    return {"reserved": True}


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal
) -> CampaignOut:
    c = await session.get(Campaign, campaign_id)
    if c is None:
        raise HTTPException(404, "not found")
    return _campaign_out(c)


@router.post("/opportunities/generate", response_model=list[OpportunityOut], status_code=201)
async def generate_opportunities_route(
    body: OpportunityGenerateIn, session: DbSession, principal: CurrentPrincipal
) -> list[OpportunityOut]:
    opps = await generate_opportunities(
        session, tenant_id=uuid.UUID(principal.tenant_id), agent_id=body.agent_id
    )
    return [OpportunityOut.model_validate(o) for o in opps]


@router.get("/opportunities", response_model=list[OpportunityOut])
async def opportunities_route(
    session: DbSession, principal: CurrentPrincipal
) -> list[OpportunityOut]:
    opps = await list_opportunities(session, uuid.UUID(principal.tenant_id))
    return [OpportunityOut.model_validate(o) for o in opps]
