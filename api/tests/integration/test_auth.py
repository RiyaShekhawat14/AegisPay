"""End-to-end auth tests: resolve a token to a principal, and reject missing/bad tokens.

Covers the Phase 2 acceptance criteria for identity + tenant: an authenticated request carries
its tenant (from the token, never supplied by the client), and unauthenticated / invalid
credentials are rejected with 401.
"""

from __future__ import annotations

import time

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from httpx import ASGITransport, AsyncClient


def _token(**overrides) -> str:
    claims = {
        "sub": "user-1",
        "type": "USER",
        "tenant_id": "tenant-alpha",
        "role": "member",
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return sign(claims, get_settings().jwt_secret)


@pytest.mark.asyncio
async def test_valid_token_returns_principal_with_tenant():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/me", headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 200
    body = r.json()
    assert body["subject"] == "user-1"
    assert body["tenant_id"] == "tenant-alpha"
    assert body["role"] == "member"


@pytest.mark.asyncio
async def test_valid_admin_token_passes_identity():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/me", headers={"Authorization": f"Bearer {_token(role='admin')}"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_missing_token_is_401():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_bad_signature_is_401_not_500():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_is_401():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get(
            "/v1/me", headers={"Authorization": f"Bearer {_token(exp=int(time.time()) - 10)}"}
        )
    assert r.status_code == 401
