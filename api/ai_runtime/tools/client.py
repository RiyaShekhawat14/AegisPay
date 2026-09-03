"""HTTP client to the AegisPay Control Plane.

This is the ONLY thing the AI runtime can do: call the control plane API. It has no database
credentials, no Razorpay secrets, and no money-move methods. Only read-only + request actions.
"""

from __future__ import annotations

import httpx


class ControlPlaneClient:
    def __init__(self, *, base_url: str, token: str = "") -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=10,
        )

    async def discover_products(self) -> list[dict]:
        r = await self._client.get("/v1/products")
        r.raise_for_status()
        return r.json()

    async def create_cart(self, *, agent_id: str) -> dict:
        r = await self._client.post("/v1/carts", json={"agent_id": agent_id})
        r.raise_for_status()
        return r.json()

    async def add_item(self, *, cart_id: str, product_id: str, quantity: int) -> dict:
        r = await self._client.post(
            f"/v1/carts/{cart_id}/items", json={"product_id": product_id, "quantity": quantity}
        )
        r.raise_for_status()
        return r.json()

    async def checkout(self, *, cart_id: str) -> dict:
        r = await self._client.post(f"/v1/carts/{cart_id}/checkout")
        r.raise_for_status()
        return r.json()

    async def request_authorization(self, *, cart_id: str) -> dict:
        r = await self._client.post("/v1/authorizations", json={"cart_id": cart_id})
        r.raise_for_status()
        return r.json()
