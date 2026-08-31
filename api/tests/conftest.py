"""Ensure `api` (and `ai_runtime`) are importable during collection.

conftest lives at <repo>/api/tests/, so parents[1] = <repo>/api and parents[2] = <repo>
(the import root for the `api` package). Added at import time so pytest can collect tests
that do `from api.… ` regardless of working directory.
"""

import sys
from pathlib import Path

import pytest

_here = Path(__file__).resolve()
for _p in (_here.parents[1], _here.parents[2]):  # api/ and repo root
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(scope="session", autouse=True)
async def dispose_engine():
    """Close the async DB engine once, on the session event loop, so asyncpg shuts down cleanly."""
    yield
    from api.db.session import engine

    await engine.dispose()
