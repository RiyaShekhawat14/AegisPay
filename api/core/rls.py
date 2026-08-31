"""Row-Level Security helpers.

Tenant context is pinned server-side per transaction. The application role cannot bypass
RLS, so every query is automatically restricted to the caller's merchant.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def pin_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Pin the RLS tenant context for the current transaction.

    Uses `set_config(..., is_local=true)` rather than `SET LOCAL` because Postgres does not
    allow a bound parameter in a SET statement. `is_local=true` keeps it transaction-scoped.
    """
    await session.execute(text("select set_config('app.tenant_id', :t, true)"), {"t": tenant_id})
