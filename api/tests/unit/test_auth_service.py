"""Password hashing (bcrypt) — roundtrip + rejection."""

from api.services.auth import hash_password, verify_password


def test_hash_roundtrip_and_reject():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_hashes_are_salted():
    assert hash_password("same") != hash_password("same")
