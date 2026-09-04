"""Auth (email/password): signup + login issue a JWT the control plane accepts."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_signup_then_login_routes():
    from api.main import app

    email = f"u{uuid.uuid4().hex[:8]}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/auth/signup", json={"email": email, "password": "secret123", "role": "member", "merchant_name": "T"})
        assert r.status_code == 201, r.text
        token = r.json()["token"]
        assert token

        # The issued JWT is accepted by /v1/me.
        me = await c.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200

        # Login with the same credentials works.
        r = await c.post("/v1/auth/login", json={"email": email, "password": "secret123"})
        assert r.status_code == 200
        assert r.json()["token"]

    # Wrong password -> 401.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/auth/login", json={"email": email, "password": "wrong"})
        assert r.status_code == 401
