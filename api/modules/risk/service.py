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


# Simple deterministic thresholds (minor units). Demo-friendly bands so realistic
# purchases auto-approve; very large amounts still require human/quorum approval.
LOW_MAX_MINOR = 300_000  # <= ₹3,000 is low risk (shoes, everyday items)
MEDIUM_MAX_MINOR = 2_000_000  # <= ₹20,000 is medium; above is high
NEW_BUYER_HIGH_MINOR = 1_500_000  # a new buyer above ₹15,000 is high


def score(
    *, amount_minor: int, is_new_buyer: bool = False, high_velocity: bool = False
) -> RiskLevel:
    if amount_minor > MEDIUM_MAX_MINOR or high_velocity:
        return RiskLevel.HIGH
    if amount_minor > LOW_MAX_MINOR or (is_new_buyer and amount_minor > NEW_BUYER_HIGH_MINOR):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
