"""Risk scoring (deterministic, no LLM)."""

from api.modules.risk.service import RiskLevel, score


def test_low_medium_high_thresholds():
    assert score(amount_minor=300_000) == RiskLevel.LOW  # <= ₹3,000
    assert score(amount_minor=500_000) == RiskLevel.MEDIUM  # <= ₹5,000 (₹20k max)
    assert score(amount_minor=2_000_000) == RiskLevel.MEDIUM  # boundary: equal to medium max
    assert score(amount_minor=2_000_001) == RiskLevel.HIGH


def test_high_velocity_always_high():
    assert score(amount_minor=5000, high_velocity=True) == RiskLevel.HIGH


def test_new_buyer_medium():
    assert score(amount_minor=500_000, is_new_buyer=True) == RiskLevel.MEDIUM
