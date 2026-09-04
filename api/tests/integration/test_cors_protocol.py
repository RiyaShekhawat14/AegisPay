"""CORS + protocol/v1 endpoint smoke: the frontend origins can preflight, and the gateway maps."""

from __future__ import annotations

import time
import uuid

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from httpx import ASGITransport, AsyncClient


def _h() -> dict[str, str]:
    t = sign(
        {
            "sub": "agent-1",
            "type": "AGENT",
            "tenant_id": str(uuid.uuid4()),
            "role": "member",
            "exp": int(time.time()) + 3600,
        },
        get_settings().jwt_secret,
    )
    return {"Authorization": f"Bearer {t}"}


@pytest.mark.asyncio
async def test_cors_preflight_allows_frontend_origin():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.options(
            "/v1/auth/login",
            headers={"Origin": "http://localhost:3002", "Access-Control-Request-Method": "POST"},
        )
    # CORSMiddleware adds the allow-origin header on preflight.
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3002"


@pytest.mark.asyncio
async def test_protocol_gateway_mcp_maps_to_action():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/protocol/mcp", headers=_h(), json={"tool": "request_authorization"})
    assert r.status_code == 200, r.text
    assert r.json()["action"] == "REQUEST_AUTH"
