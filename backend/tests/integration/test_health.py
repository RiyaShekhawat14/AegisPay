import pytest


@pytest.mark.asyncio
async def test_app_health():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
