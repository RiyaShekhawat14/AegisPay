"""Deterministic policy engine.

Same facts, same decision. The LLM never evaluates or edits policy — only a merchant
policy admin can, and every change is versioned and audited.

Decision values:
  ALLOW | DENY | HUMAN_APPROVAL_REQUIRED | STEP_UP_AUTHENTICATION
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    STEP_UP_AUTHENTICATION = "STEP_UP_AUTHENTICATION"


@dataclass(frozen=True)
class Rule:
    dimension: str    # amount | category | hour | daily_total | agent
    operator: str     # lte | gte | eq | in | not_in | between
    value: object
    effect: Decision
    precedence: int = 100


@dataclass(frozen=True)
class Facts:
    amount_minor: int
    category: str
    hour: int
    agent_daily_spent_minor: int


class Policy:
    """A compiled, immutable version of a policy (merchant-owned)."""

    def __init__(self, version: str, rules: list[Rule]) -> None:
        self.version = version
        # DENY always sinks to the bottom (highest precedence) so it wins.
        self._rules = sorted(rules, key=lambda r: (0 if r.effect == Decision.DENY else 1, r.precedence))

    def evaluate(self, f: Facts) -> tuple[Decision, list[str]]:
        reasons: list[str] = []
        for rule in self._rules:
            if _matches(rule, f):
                reasons.append(f"{rule.dimension} -> {rule.effect.value}")
                return rule.effect, reasons
        return Decision.ALLOW, reasons


def _matches(rule: Rule, f: Facts) -> bool:
    val = {
        "amount": f.amount_minor,
        "category": f.category,
        "hour": f.hour,
        "daily_total": f.agent_daily_spent_minor,
    }[rule.dimension]
    op, v = rule.operator, rule.value
    if op == "lte":
        return val <= v
    if op == "gte":
        return val >= v
    if op == "eq":
        return val == v
    if op == "in":
        return val in v
    if op == "not_in":
        return val not in v
    if op == "between":
        return v[0] <= val <= v[1]
    return False
