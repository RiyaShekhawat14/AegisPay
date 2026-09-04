"""Protocol Gateway (Phase 12): external protocol -> canonical intent, never a money action."""

from __future__ import annotations

import time
import uuid

import pytest
from api.core.config import get_settings
from api.core.jwt import sign
from httpx import ASGITransport, AsyncClient


def _token() -> str:
    return sign(
        {
            "sub": "agent-1",
            "type": "AGENT",
            "tenant_id": str(uuid.uuid4()),
            "role": "member",
            "exp": int(time.time()) + 3600,
        },
        get_settings().jwt_secret,
    )


@pytest.mark.asyncio
async def test_mcp_message_maps_to_canonical():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/v1/protocol/mcp",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"tool": "add_to_cart", "args": {"product_id": "p1"}},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["protocol"] == "MCP"
    assert body["action"] == "ADD_TO_CART"
    assert body["agent_id"] is not None


@pytest.mark.asyncio
async def test_a2a_purchase_maps_to_request_auth():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/v1/protocol/a2a",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"task": {"kind": "purchase"}},
        )
    assert r.status_code == 200
    assert r.json()["action"] == "REQUEST_AUTH"


@pytest.mark.asyncio
async def test_unsupported_protocol_rejected():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/v1/protocol/nope", headers={"Authorization": f"Bearer {_token()}"}, json={}
        )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_requires_auth():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/v1/protocol/mcp", json={"tool": "search_catalog"})
    assert r.status_code == 401
