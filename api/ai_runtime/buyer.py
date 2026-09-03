"""SELL buyer flow: discover -> cart -> items -> checkout -> request authorization.

The AI buyer sets up the purchase and REQUESTS authorization. It never calls a payment /
capture / refund tool — those live only in the control plane. The report handed back lets the
control plane (or a human) decide whether to proceed.
"""

from __future__ import annotations

from ai_runtime.schemas import CommerceIntent
from ai_runtime.tools.registry import is_allowed

# Every tool the buyer uses must pass the allowlist; no money-move tools exist.
_BUYER_TOOLS = ("discover_products", "create_cart", "add_item", "checkout", "request_authorization")


async def run_buyer(intent: CommerceIntent, client) -> dict:
    assert all(is_allowed(t) for t in _BUYER_TOOLS), "buyer uses a non-allowed tool"
    catalog = await client.discover_products()
    cart = await client.create_cart(agent_id=intent.agent_id)
    cart_id = str(cart["id"])
    for item in intent.items:
        await client.add_item(cart_id=cart_id, product_id=item.product_id, quantity=item.quantity)
    order = await client.checkout(cart_id=cart_id)
    authz = await client.request_authorization(cart_id=cart_id)
    return {
        "order_id": order.get("id"),
        "authorization_id": authz.get("id"),
        "authorization_status": authz.get("status"),
        "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in intent.items],
        "_catalog_count": len(catalog),
    }
