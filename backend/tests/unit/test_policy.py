from app.modules.policy.engine import Decision, Facts, Policy, Rule


def _policy(version="v1"):
    return Policy(version, [
        Rule("category", "in", ["alcohol", "tobacco"], Decision.DENY, precedence=0),
        Rule("amount", "gte", 200_000, Decision.HUMAN_APPROVAL_REQUIRED, precedence=10),
        Rule("amount", "gte", 500_000, Decision.STEP_UP_AUTHENTICATION, precedence=5),
        Rule("daily_total", "lte", 1_000_000, Decision.ALLOW),
    ])


def test_deny_category_wins():
    d, _ = _policy().evaluate(Facts(10_000, "tobacco", 12, 0))
    assert d == Decision.DENY


def test_human_approval_over_threshold():
    d, _ = _policy().evaluate(Facts(250_000, "food", 12, 0))
    assert d == Decision.HUMAN_APPROVAL_REQUIRED


def test_allow_within_limits():
    d, _ = _policy().evaluate(Facts(90_000, "food", 12, 50_000))
    assert d == Decision.ALLOW


def test_deterministic_same_input():
    a = _policy().evaluate(Facts(90_000, "food", 12, 50_000))[0]
    b = _policy().evaluate(Facts(90_000, "food", 12, 50_000))[0]
    assert a == b
