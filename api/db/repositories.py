"""Tenant-scoped repositories. Every query/change runs within the tenant-pinned session, so
RLS restricts it to the caller's merchant even on a bug. Money mutations are transactional.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import Base, Campaign, Order, Payment

T = TypeVar("T", bound=Base)


class BaseRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        return obj


class OrderRepo(BaseRepo):
    async def get(self, order_id: uuid.UUID) -> Order | None:
        return await self.session.get(Order, order_id)

    async def idempotent_by_key(self, key: str) -> Order | None:
        res = await self.session.execute(select(Order).where(Order.idempotency_key == key))
        return res.scalar_one_or_none()


class PaymentRepo(BaseRepo):
    async def get(self, payment_id: uuid.UUID) -> Payment | None:
        return await self.session.get(Payment, payment_id)

    async def update_status(self, payment_id: uuid.UUID, status: str) -> Payment | None:
        p = await self.session.get(Payment, payment_id)
        if p is None:
            return None
        p.status = status
        if status == "UNKNOWN" and p.unknown_since is None:
            p.unknown_since = datetime.now(UTC)
        await self.session.flush()
        return p


class CampaignRepo(BaseRepo):
    """Atomic budget reservation: serialize on the row; never allow overspend."""

    async def atomic_reserve(self, campaign_id: uuid.UUID, cost_minor: int) -> bool:
        row = (
            await self.session.execute(
                select(Campaign).where(Campaign.id == campaign_id).with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            return False
        row.spent_minor += cost_minor
        if row.spent_minor > row.budget_minor:
            row.spent_minor -= cost_minor
            return False
        await self.session.flush()
        return True
