"""Canonical AegisPay Intent — the single normalized contract the control plane accepts.

Every external protocol is reduced to this. There is exactly one form the control plane
understands, so a new protocol is only ever a new adapter, never a new money path.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Actions the control plane will execute. Money is NOT among them — no adapter may yield one.
ALLOWED_ACTIONS = frozenset(
    {
        "DISCOVER",
        "GET_PRODUCT",
        "RECOMMEND",
        "COMPARE",
        "ADD_TO_CART",
        "REMOVE_FROM_CART",
        "CALCULATE_TOTAL",
        "CHECKOUT",
        "REQUEST_AUTH",
        "REQUEST_HUMAN_APPROVAL",
    }
)

# Actions that move money are NEVER produced by a protocol adapter.
FORBIDDEN_ACTIONS = frozenset({"EXECUTE_PAYMENT", "ISSUE_REFUND", "MODIFY_ORDER", "UPDATE_POLICY"})


@dataclass(frozen=True)
class CanonicalIntent:
    protocol: str
    agent_id: str
    merchant_id: str
    subject: str  # actor that authorized (user id / mandate ref)
    action: str
    payload: dict = field(default_factory=dict)

    def validate(self) -> None:
        if self.action in FORBIDDEN_ACTIONS:
            raise ValueError(f"protocol {self.protocol} attempted forbidden action {self.action}")
        if self.action not in ALLOWED_ACTIONS:
            raise ValueError(f"unknown action {self.action}")
