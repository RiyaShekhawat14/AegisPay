from api.core.ratelimit import MemRateStore, allow


def test_rate_limit_enforced_per_window():
    s = MemRateStore()
    for _ in range(5):
        assert allow(s, "agent:123", limit=5, window=60) is True
    assert allow(s, "agent:123", limit=5, window=60) is False


def test_rate_limit_isolated_by_key():
    s = MemRateStore()
    assert allow(s, "a", limit=1, window=60) is True
    assert allow(s, "b", limit=1, window=60) is True
