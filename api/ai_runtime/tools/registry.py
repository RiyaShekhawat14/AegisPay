"""Tool allowlist for the AI runtime.

The AI can only use read-only lookups and REQUEST actions. It has NO money tools: it can
never capture, refund, or execute a payment. This belongs to the control plane only.
"""

from __future__ import annotations

ALLOWED_TOOLS = {
    "discover_products",
    "create_cart",
    "add_item",
    "checkout",
    "request_authorization",
}

# Money-moving actions the AI must NEVER have, no matter what.
FORBIDDEN_TOOLS = {"execute_payment", "capture", "refund", "policy.write"}


def is_allowed(tool: str) -> bool:
    return tool in ALLOWED_TOOLS


def is_forbidden(tool: str) -> bool:
    return tool in FORBIDDEN_TOOLS
