"""Refund guards. Refunds are controlled: capped to captured, single effective per key,
and always gated by policy/authorization. The AI has no unrestricted refund tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RefundLedger(Protocol):
    def applied(self, idempotency_key: str) -> bool: ...
    def record(self, idempotency_key: str) -> None: ...


@dataclass(frozen=True)
class RefundDecision:
    allowed: bool
    reason: str


def decide(
    *,
    amount_minor: int,
    captured_minor: int,
    refunded_minor: int,
    requested_by: str,
    human_only: bool = True,
    ledger: RefundLedger,
    key: str,
) -> RefundDecision:
    if amount_minor <= 0:
        return RefundDecision(False, "amount must be positive")
    if amount_minor > captured_minor - refunded_minor:
        return RefundDecision(False, "refund exceeds captured balance")
    if ledger.applied(key):
        return RefundDecision(False, "duplicate refund key")  # single effective refund per key
    if human_only and requested_by.startswith("ai:"):
        return RefundDecision(False, "AI cannot issue unrestricted refunds")
    return RefundDecision(True, "ok")
