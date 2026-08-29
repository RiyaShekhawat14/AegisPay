"""Async SQLAlchemy session with tenant context + RLS.

Tenant is pinned server-side per transaction via SET LOCAL app.tenant_id. The app role
cannot bypass RLS, so the database enforces tenant isolation. A request dependency reads the
tenant set by the middleware and opens a session pinned to it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.core.config import get_settings
from api.core.logging import tenant_id_ctx

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def pin_tenant(session: AsyncSession, tenant_id: str) -> None:
    await session.execute(text("SET LOCAL app.tenant_id = :t"), {"t": tenant_id})


@asynccontextmanager
async def tenant_session(tenant_id: str) -> AsyncIterator[AsyncSession]:
    async with Session() as session:
        await pin_tenant(session, tenant_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: session pinned to the request's tenant (from middleware context)."""
    async with Session() as session:
        tenant = tenant_id_ctx.get()
        if tenant:
            await pin_tenant(session, tenant)
        yield session
