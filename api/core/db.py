"""Async SQLAlchemy setup.

Tenant isolation is enforced in the database (Row-Level Security). The application role
cannot bypass RLS; each request sets the tenant context server-side with SET LOCAL so that
RLS restricts every query to the authenticated merchant's rows. The frontend never decides
the tenant — it is derived from the authenticated identity.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.core.config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10)
Session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def tenant_session(tenant_id: str) -> AsyncIterator[AsyncSession]:
    """Open a session with the tenant context pinned for the whole transaction."""
    async with Session() as session:
        await session.execute(text("SET LOCAL app.tenant_id = :t"), {"t": tenant_id})
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
