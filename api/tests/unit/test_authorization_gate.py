"""Authorization gate: policy -> risk -> decision (pure, no DB)."""

from api.modules.authorization.service import evaluate, required_approvals
from api.modules.risk.service import RiskLevel


def test_low_amount_auto_allow():
    ev = evaluate(amount_minor=5000)
    assert ev.decision == "ALLOW"
    assert ev.risk is RiskLevel.LOW


def test_high_amount_requires_human():
    ev = evaluate(amount_minor=200_000)
    assert ev.decision == "HUMAN_APPROVAL_REQUIRED"
    assert ev.risk is RiskLevel.HIGH


def test_over_cap_is_denied():
    ev = evaluate(amount_minor=6_000_000)
    assert ev.decision == "DENY"


def test_blocked_category_is_denied():
    ev = evaluate(amount_minor=5000, category="weapons")
    assert ev.decision == "DENY"


def test_required_approvals_per_risk():
    assert required_approvals(RiskLevel.HIGH) == 2
    assert required_approvals(RiskLevel.MEDIUM) == 1
    assert required_approvals(RiskLevel.LOW) == 0
