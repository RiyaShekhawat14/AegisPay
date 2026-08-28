"""Row-Level Security helpers.

Tenant context is pinned server-side per transaction. The application role cannot bypass
RLS, so every query is automatically restricted to the caller's merchant.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def pin_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Pin the RLS tenant context for the current transaction."""
    await session.execute(text("SET LOCAL app.tenant_id = :t"), {"t": tenant_id})
