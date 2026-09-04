"""Risk scoring (deterministic, no LLM)."""

from api.modules.risk.service import RiskLevel, score


def test_low_medium_high_thresholds():
    assert score(amount_minor=5000) == RiskLevel.LOW
    assert score(amount_minor=50_000) == RiskLevel.MEDIUM
    assert score(amount_minor=100_000) == RiskLevel.MEDIUM  # boundary: equal to medium max
    assert score(amount_minor=100_001) == RiskLevel.HIGH


def test_high_velocity_always_high():
    assert score(amount_minor=5000, high_velocity=True) == RiskLevel.HIGH


def test_new_buyer_medium():
    assert score(amount_minor=20_000, is_new_buyer=True) == RiskLevel.MEDIUM
