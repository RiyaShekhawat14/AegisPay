"""Core API wiring (Phase 3): app boots, health probes, and a CONSISTENT error envelope.

The whole app + middleware is exercised in-process via ASGITransport. Application-level errors
(authentication, domain errors) share one envelope: {"code","message","request_id","retryable"},
and request_id flows through every response.

Note: FastAPI's router-level 404 (unknown route) and uncaught 500 (which ASGITransport re-raises)
are framework behaviors, so consistency for HTTP status -> code is covered by unit tests on the
mapping helper instead.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def client():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _envelope() -> set[str]:
    return {"code", "message", "request_id", "retryable"}


@pytest.mark.asyncio
async def test_health_ok(client):
    r = await client.get("/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_live_ok(client):
    r = await client.get("/v1/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_reports_db_ready(client):
    # requires DATABASE_URL (postgres) reachable; returns 200 only when the DB answers.
    r = await client.get("/v1/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_health_sets_request_id_header(client):
    r = await client.get("/v1/health")
    assert r.headers.get("x-request-id")


@pytest.mark.asyncio
async def test_unauthorized_uses_envelope(client):
    r = await client.get("/v1/me")
    assert r.status_code == 401
    body = r.json()
    assert set(body) == _envelope()
    assert body["code"] == "AUTHENTICATION_ERROR"
    assert body["request_id"]
