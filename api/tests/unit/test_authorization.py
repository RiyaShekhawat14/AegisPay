from api.core.authorization import FOREVER_FORBIDDEN, ScopedAgent, has_permission


def test_rbac_role_permissions():
    assert has_permission("admin", "anything") is True
    assert has_permission("approver", "approval.decide") is True
    assert has_permission("member", "policy.write") is False


def test_agent_is_scoped_and_cannot_elevate():
    agent = ScopedAgent(
        "a1", "t1", allowed_tools={"search_catalog", "add_to_cart"}, scopes={"discover", "cart"}
    )
    assert agent.can_access("search_catalog", "discover", "catalog.read") is True
    assert agent.can_access("execute_payment", "cart", "payment.execute") is False  # out of scope
    assert agent.can_access("search_catalog", "payments", "catalog.read") is False  # scope mismatch


def test_agent_cannot_hold_forbidden_permission():
    agent = ScopedAgent("a1", "t1", allowed_tools={"any"}, scopes={"*"})
    assert agent.can_access("any", "*", "refund.execute") is False
    assert agent.can_access("any", "*", "policy.write") is False
    for perm in FOREVER_FORBIDDEN:
        assert agent.can_access("any", "*", perm) is False
