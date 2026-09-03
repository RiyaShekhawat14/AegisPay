"""The agent: compile an intent into a safe plan of ALLOWED actions.

The AI REASONS and REQUESTS: it turns a user intent into a list of `request_authorization`
actions (plus a read-only catalog lookup). It never executes payment/capture/refund — those
live in the control plane. The money gate still decides.
"""

from __future__ import annotations

from ai_runtime.schemas import CommerceIntent
from ai_runtime.tools.registry import is_allowed


async def run_agent(intent: CommerceIntent, client) -> dict:
    catalog = await _safe_catalog(client)  # read-only; degrade gracefully if unavailable
    actions = []
    for item in intent.items:
        tool = "request_authorization"  # the only allowed action here; no money moves
        if not is_allowed(tool):
            continue
        actions.append({"tool": tool, "product_id": item.product_id, "quantity": item.quantity})
    return {
        "kind": intent.kind,
        "summary": intent.summary,
        "catalog_count": len(catalog),
        "actions": actions,
    }


async def _safe_catalog(client) -> list:
    try:
        return await client.discover_products()
    except Exception:  # noqa: BLE001 - recommendation degrades if the control plane is unreachable
        return []
