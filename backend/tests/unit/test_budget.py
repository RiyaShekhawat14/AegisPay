from app.modules.campaigns.budget import Budget, Caps, check_caps, reserve


def test_atomic_reserve_never_overspends():
    b = Budget(limit_minor=5000)
    assert reserve(b, 3000) is True
    assert reserve(b, 2000) is True
    assert reserve(b, 1) is False  # exhausted
    assert b.spent_minor == 5000


def test_caps_reject_discount_and_margin():
    caps = Caps(max_discount_pct=10, min_margin_pct=18, max_duration_days=30)
    assert check_caps(caps, discount_pct=25, margin_pct=12, duration_days=45) != []
    assert check_caps(caps, discount_pct=5, margin_pct=20, duration_days=7) == []


def test_budget_cannot_go_negative():
    b = Budget(limit_minor=100)
    assert reserve(b, 200) is False
    assert b.remaining == 100
