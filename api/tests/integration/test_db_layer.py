"""Database integration tests: prove tenant isolation (RLS) and repository behavior.

These run against a migrated Postgres (see deploy/compose). DATABASE_URL must point at the
`aegispay_app` role (never a superuser), which is how RLS is enforced in production.
"""

from __future__ import annotations

import uuid

import pytest
from api.core.rls import pin_tenant
from api.db.models import Campaign
from api.db.repositories import CampaignRepo
from api.db.session import Session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

_TENANT_SQL = "insert into tenants (id, slug, name) values (:id, :slug, :name)"
_AGENT_SQL = "insert into agents (id, tenant_id, name, type) values (:id, :tenant_id, :name, :type)"
_PRODUCT_SQL = (
    "insert into products (id, tenant_id, sku, name, price_minor) "
    "values (:id, :tenant_id, :sku, :name, :price)"
)
_CAMPAIGN_SQL = (
    "insert into campaigns (id, tenant_id, agent_id, name, budget_minor, status) "
    "values (:id, :tenant_id, :agent_id, :name, :budget, 'ACTIVE')"
)


async def _new_tenant() -> uuid.UUID:
    """tenants has no RLS, so the app role can create one without a tenant context."""
    identifier = uuid.uuid4()
    async with Session() as session:
        await session.execute(
            text(_TENANT_SQL),
            {"id": identifier, "slug": f"slug-{identifier}", "name": f"Tenant {identifier}"},
        )
        await session.commit()
    return identifier


async def _new_agent(tenant_id: uuid.UUID) -> uuid.UUID:
    agent_id = uuid.uuid4()
    async with Session() as session:
        await pin_tenant(session, str(tenant_id))
        await session.execute(
            text(_AGENT_SQL),
            {"id": agent_id, "tenant_id": tenant_id, "name": "agent", "type": "SELL"},
        )
        await session.commit()
    return agent_id


async def _insert(session, sql: str, **params) -> None:
    await session.execute(text(sql), params)


@pytest.mark.asyncio
async def test_rls_isolates_tenants() -> None:
    tenant_a, tenant_b = await _new_tenant(), await _new_tenant()

    # A product is only visible (and only writable) when the RLS context is that tenant.
    product_a, product_b = uuid.uuid4(), uuid.uuid4()
    async with Session() as session:
        await pin_tenant(session, str(tenant_a))
        await _insert(
            session, _PRODUCT_SQL, id=product_a, tenant_id=tenant_a, sku="A1", name="A", price=100
        )
        await session.commit()
    async with Session() as session:
        await pin_tenant(session, str(tenant_b))
        await session.execute(
            text(_PRODUCT_SQL),
            {"id": product_b, "tenant_id": tenant_b, "sku": "B1", "name": "B", "price": 200},
        )
        await session.commit()

    async with Session() as session:
        await pin_tenant(session, str(tenant_a))
        rows = (await session.execute(text("select id from products"))).scalars().all()
        assert set(rows) == {product_a}

    async with Session() as session:
        await pin_tenant(session, str(tenant_b))
        rows = (await session.execute(text("select id from products"))).scalars().all()
        assert set(rows) == {product_b}


@pytest.mark.asyncio
async def test_writes_require_a_tenant_context() -> None:
    """Without a tenant context (RLS), the app role cannot insert into a tenant-owned table."""
    tenant = await _new_tenant()
    with pytest.raises(ProgrammingError):
        async with Session() as session:
            await session.execute(
                text(_PRODUCT_SQL),
                {"id": uuid.uuid4(), "tenant_id": tenant, "sku": "X", "name": "X", "price": 1},
            )
            await session.commit()


@pytest.mark.asyncio
async def test_campaign_repo_reserve_never_overspends() -> None:
    tenant = await _new_tenant()
    agent = await _new_agent(tenant)
    campaign = uuid.uuid4()
    async with Session() as session:
        await pin_tenant(session, str(tenant))
        await session.execute(
            text(_CAMPAIGN_SQL),
            {
                "id": campaign,
                "tenant_id": tenant,
                "agent_id": agent,
                "name": "Launch",
                "budget": 1000,
            },
        )
        await session.commit()

    async with Session() as session:
        await pin_tenant(session, str(tenant))
        repo = CampaignRepo(session)
        assert await repo.atomic_reserve(campaign, 400) is True
        assert await repo.atomic_reserve(campaign, 400) is True
        assert await repo.atomic_reserve(campaign, 400) is False  # would exceed 1000
        # Read before commit: SET LOCAL app.tenant_id is transaction-scoped and is cleared
        # on commit, so the row must be read within the pinned transaction.
        spent = (
            await session.execute(
                text("select spent_minor from campaigns where id = :id"), {"id": campaign}
            )
        ).scalar_one()
        assert spent == 800
        await session.commit()


@pytest.mark.asyncio
async def test_campaign_model_maps_to_table() -> None:
    tenant = await _new_tenant()
    agent = await _new_agent(tenant)
    campaign = uuid.uuid4()
    async with Session() as session:
        await pin_tenant(session, str(tenant))
        await session.execute(
            text(_CAMPAIGN_SQL),
            {
                "id": campaign,
                "tenant_id": tenant,
                "agent_id": agent,
                "name": "Launch",
                "budget": 500,
            },
        )
        await session.commit()

    async with Session() as session:
        await pin_tenant(session, str(tenant))
        row = await session.get(Campaign, campaign)
        assert row is not None
        assert row.id == campaign
        assert row.budget_minor == 500
