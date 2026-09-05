"""Password reset flow: request -> redeem -> single-use, plus weak-password rejection."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_full_password_reset_flow():
    from api.main import app

    email = f"reset{uuid.uuid4().hex[:8]}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/v1/auth/signup",
            json={"email": email, "password": "secret123", "role": "member", "merchant_name": "T"},
        )
        assert r.status_code == 201

        # Request a reset; in dev the token is returned.
        r = await c.post("/v1/auth/forgot-password", json={"email": email})
        assert r.status_code == 200
        token = r.json()["reset_token"]
        assert token

        # Old password still works before reset.
        r = await c.post("/v1/auth/login", json={"email": email, "password": "secret123"})
        assert r.status_code == 200

        # Reset to a new password.
        r = await c.post("/v1/auth/reset-password", json={"token": token, "password": "NewPass123"})
        assert r.status_code == 200

        # Token is single-use: replaying it must fail.
        r = await c.post("/v1/auth/reset-password", json={"token": token, "password": "NewPass456"})
        assert r.status_code == 401

        # New password works; old password is now invalid.
        r = await c.post("/v1/auth/login", json={"email": email, "password": "NewPass123"})
        assert r.status_code == 200
        r = await c.post("/v1/auth/login", json={"email": email, "password": "secret123"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_does_not_enumerate_and_rejects_weak():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # Unknown email: generic message, no token.
        r = await c.post("/v1/auth/forgot-password", json={"email": "ghost@test.com"})
        assert r.status_code == 200
        body = r.json()
        assert body["message"]
        assert body["reset_token"] == ""

        # Weak new password is rejected.
        r = await c.post("/v1/auth/reset-password", json={"token": "some-token", "password": "abc"})
        assert r.status_code == 422
