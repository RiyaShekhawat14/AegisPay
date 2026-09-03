"""Observability (Phase 17): the control plane exposes Prometheus metrics + a health probe."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_emits_prometheus_text():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.get("/v1/health")
        r = await c.get("/v1/metrics")
    assert r.status_code == 200
    text = r.text
    assert "# TYPE http_requests_total counter" in text
    assert 'http_requests_total{path="/v1/health",status="200"}' in text
