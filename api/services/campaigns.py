"""GROW campaign service: create a campaign (caps-checked) and reserve budget atomically.

Reuses `campaigns/budget.py` (check_caps for merchant caps) and the tested
`CampaignRepo.atomic_reserve` (never overspends, even under concurrency).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import ValidationError
from api.db.models import Campaign
from api.db.repositories import CampaignRepo
from api.modules.campaigns.budget import Caps, check_caps

DEFAULT_CAPS = Caps(max_discount_pct=20, min_margin_pct=15, max_duration_days=30)


async def create_campaign(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    name: str,
    budget_minor: int,
    discount_pct: float = 0,
    margin_pct: float = 0,
    duration_days: int = 0,
) -> Campaign:
    reasons = check_caps(
        DEFAULT_CAPS, discount_pct=discount_pct, margin_pct=margin_pct, duration_days=duration_days
    )
    if reasons:
        raise ValidationError("; ".join(reasons))
    campaign = Campaign(
        tenant_id=tenant_id,
        agent_id=agent_id,
        name=name,
        budget_minor=budget_minor,
        discount_pct=discount_pct or None,
        min_margin_pct=margin_pct or None,
        status="ACTIVE",
    )
    session.add(campaign)
    await session.flush()
    return campaign


async def reserve_budget(session: AsyncSession, campaign_id: uuid.UUID, cost_minor: int) -> bool:
    """Reserve `cost_minor` from the campaign budget. False when it would overspend."""
    return await CampaignRepo(session).atomic_reserve(campaign_id, cost_minor)
