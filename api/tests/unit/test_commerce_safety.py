from datetime import UTC, datetime, timedelta

from api.modules.commerce.safety import CartLine, cart_hash, validate


def _lines():
    return [CartLine("p1", 2, 1000, "v1"), CartLine("p2", 1, 500, "v1")]


def test_hash_matches_expected():
    assert cart_hash(_lines())


def test_price_change_invalidates():
    h = cart_hash(_lines())
    changed = [CartLine("p1", 2, 1000, "v2"), CartLine("p2", 1, 500, "v1")]  # price_version changed
    assert cart_hash(changed) != h


def test_quantity_change_invalidates():
    h = cart_hash(_lines())
    assert cart_hash([CartLine("p1", 3, 1000, "v1"), CartLine("p2", 1, 500, "v1")]) != h


def test_validate_expired_cart_rejected():
    now = datetime.now(UTC).isoformat()
    past = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    future = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
    assert (
        validate(
            _lines(),
            expected_hash=cart_hash(_lines()),
            price_version="v1",
            auth_price_version="v1",
            cart_expires_at=past,
            auth_expires_at=future,
            now=now,
        )
        is False
    )


def test_validate_ok():
    now = datetime.now(UTC).isoformat()
    future = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
    assert (
        validate(
            _lines(),
            expected_hash=cart_hash(_lines()),
            price_version="v1",
            auth_price_version="v1",
            cart_expires_at=future,
            auth_expires_at=future,
            now=now,
        )
        is True
    )
