"""GROW opportunities: deterministic growth suggestions from the catalog.

The AI "recommends" but the suggestions are generated deterministically here and persisted;
the merchant/AI can act on them, but budget/policy still gate any spend.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import Opportunity
from api.db.repositories import ProductRepo


async def generate_opportunities(
    session: AsyncSession, *, tenant_id: uuid.UUID, agent_id: uuid.UUID
) -> list[Opportunity]:
    products = await ProductRepo(session).list()
    created: list[Opportunity] = []
    for product in products:
        if product.status != "ACTIVE":
            continue
        opp = Opportunity(
            tenant_id=tenant_id,
            agent_id=agent_id,
            kind="cross_sell",
            anchor_product=product.id,
            target_products=[],
            confidence=0.8,
            status="OPEN",
        )
        session.add(opp)
        created.append(opp)
    await session.flush()
    return created


async def list_opportunities(session: AsyncSession, tenant_id: uuid.UUID) -> list[Opportunity]:
    res = await session.execute(
        select(Opportunity)
        .where(Opportunity.tenant_id == tenant_id)
        .order_by(Opportunity.created_at.desc())
    )
    return list(res.scalars().all())
