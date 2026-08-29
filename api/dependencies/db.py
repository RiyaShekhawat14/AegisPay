"""Database session dependency (tenant-pinned via middleware context)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_session

DbSession = Annotated[AsyncSession, Depends(get_session)]
