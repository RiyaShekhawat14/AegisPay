"""AI Runtime (Phase 9): isolation guarantees + safe agent plan.

The AI runtime can only reason/recommend/request via the control plane. It has no money tools,
no DB credentials, no payment secrets. These tests lock down those guarantees.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ai_runtime.agent import run_agent
from ai_runtime.main import app, get_client
from ai_runtime.schemas import CommerceIntent, IntentItem
from ai_runtime.tools.client import ControlPlaneClient
from ai_runtime.tools.registry import is_allowed, is_forbidden


class FakeClient:
    """Stand-in that records calls; the AI never actually moves money."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def discover_products(self) -> list[dict]:
        self.calls.append("discover_products")
        return [{"id": "p1"}]

    async def create_cart(self, *, agent_id: str) -> dict:
        self.calls.append("create_cart")
        return {"id": "c1"}

    async def add_item(self, *, cart_id: str, product_id: str, quantity: int) -> dict:
        self.calls.append("add_item")
        return {"id": cart_id}

    async def checkout(self, *, cart_id: str) -> dict:
        self.calls.append("checkout")
        return {"id": "o1"}

    async def request_authorization(self, *, cart_id: str) -> dict:
        self.calls.append("request_authorization")
        return {"id": "a1", "status": "PENDING_APPROVAL"}


def test_tool_allowlist_has_no_money_tools():
    assert is_allowed("discover_products") is True
    assert is_allowed("request_authorization") is True
    assert is_allowed("execute_payment") is False
    assert is_allowed("refund") is False
    assert is_forbidden("execute_payment") is True
    assert is_forbidden("policy.write") is True


def test_client_has_no_money_methods():
    client = ControlPlaneClient(base_url="http://localhost", token="t")
    assert hasattr(client, "discover_products")
    assert hasattr(client, "create_cart")
    assert hasattr(client, "request_authorization")
    assert not hasattr(client, "capture")
    assert not hasattr(client, "refund")
    assert not hasattr(client, "execute_payment")


@pytest.mark.asyncio
async def test_run_agent_only_requests_authorization():
    intent = CommerceIntent(
        agent_id="a1",
        kind="buy",
        summary="buy shoes",
        items=[IntentItem(product_id="p1", quantity=2)],
    )
    client = FakeClient()
    result = await run_agent(intent, client)
    assert result["catalog_count"] == 1
    assert result["actions"][0]["tool"] == "request_authorization"
    assert is_allowed(result["actions"][0]["tool"])
    # The AI only reads the catalog and requests; it never captured/refunded.
    assert "capture" not in client.calls
    assert "refund" not in client.calls


@pytest.mark.asyncio
async def test_agent_run_endpoint_returns_a_plan_with_fake_client():
    app.dependency_overrides[get_client] = lambda: FakeClient()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/agent/run",
                json={
                    "agent_id": "a1",
                    "kind": "buy",
                    "summary": "x",
                    "items": [{"product_id": "p1", "quantity": 2}],
                },
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["kind"] == "buy"
        assert body["catalog_count"] == 1
        assert body["actions"][0]["tool"] == "request_authorization"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_agent_run_validates_input():
    app.dependency_overrides[get_client] = lambda: FakeClient()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/agent/run",
                json={
                    "agent_id": "a1",
                    "kind": "buy",
                    "items": [{"product_id": "p1", "quantity": 0}],
                },
            )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_buyer_flow_requests_authorization_not_payment():
    from ai_runtime.buyer import run_buyer

    intent = CommerceIntent(
        agent_id="a1",
        kind="buy",
        summary="buy shoes",
        items=[IntentItem(product_id="p1", quantity=2)],
    )
    client = FakeClient()
    report = await run_buyer(intent, client)
    assert report["order_id"] == "o1"
    assert report["authorization_id"] == "a1"
    assert report["authorization_status"] == "PENDING_APPROVAL"
    # The buyer set up the purchase and requested authorization — never paid/captured/refunded.
    assert "capture" not in client.calls
    assert "refund" not in client.calls
    assert "execute_payment" not in client.calls
    # Every tool used is in the allowlist.
    assert all(is_allowed(t) for t in client.calls)


@pytest.mark.asyncio
async def test_buyer_endpoint_returns_report_with_fake_client():
    app.dependency_overrides[get_client] = lambda: FakeClient()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/agent/buy",
                json={"agent_id": "a1", "items": [{"product_id": "p1", "quantity": 2}]},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["order_id"] == "o1"
        assert body["authorization_status"] == "PENDING_APPROVAL"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_buyer_endpoint_validates_input():
    app.dependency_overrides[get_client] = lambda: FakeClient()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/agent/buy",
                json={"agent_id": "a1", "items": [{"product_id": "p1", "quantity": 0}]},
            )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()
