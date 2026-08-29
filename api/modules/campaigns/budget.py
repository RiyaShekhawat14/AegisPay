"""GROW campaign budget guards: atomic reservation + deterministic caps.

The AI can never raise its own budget or bypass merchant policy — these are fixed caps
checked here, and only a merchant/policy admin can change them (audited).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Caps:
    max_discount_pct: float
    min_margin_pct: float
    max_duration_days: int


@dataclass
class Budget:
    limit_minor: int
    spent_minor: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit_minor - self.spent_minor)


def reserve(budget: Budget, cost_minor: int) -> bool:
    """Atomic reservation: only succeeds if the envelope can cover the cost. Serialize on the row."""
    if cost_minor < 0 or cost_minor > budget.remaining:
        return False
    budget.spent_minor += cost_minor
    return True


def check_caps(
    caps: Caps, *, discount_pct: float, margin_pct: float, duration_days: int
) -> list[str]:
    reasons: list[str] = []
    if discount_pct > caps.max_discount_pct:
        reasons.append("discount exceeds cap")
    if margin_pct < caps.min_margin_pct:
        reasons.append("margin below floor")
    if duration_days > caps.max_duration_days:
        reasons.append("duration exceeds cap")
    return reasons
