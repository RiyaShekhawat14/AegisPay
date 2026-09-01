"""Risk scoring: deterministic facts -> LOW / MEDIUM / HIGH.

No LLM: same facts, same level. High risk requires human approval; medium may step-up;
low auto-approves. Amounts are in minor units (paisa).
"""

from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Simple deterministic thresholds (minor units).
LOW_MAX_MINOR = 10_000  # <= this is low
MEDIUM_MAX_MINOR = 100_000  # <= this is medium; above is high
NEW_BUYER_HIGH_MINOR = 10_000  # a new buyer above this is high, even under MEDIUM_MAX


def score(
    *, amount_minor: int, is_new_buyer: bool = False, high_velocity: bool = False
) -> RiskLevel:
    if amount_minor > MEDIUM_MAX_MINOR or high_velocity:
        return RiskLevel.HIGH
    if amount_minor > LOW_MAX_MINOR or (is_new_buyer and amount_minor > NEW_BUYER_HIGH_MINOR):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
