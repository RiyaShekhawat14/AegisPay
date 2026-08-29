import time

import pytest
from api.core.jwt import sign, verify


def test_sign_verify_roundtrip():
    t = sign(
        {
            "sub": "u1",
            "type": "USER",
            "tenant_id": "t1",
            "role": "admin",
            "exp": int(time.time()) + 100,
        },
        "s",
    )
    assert verify(t, "s")["sub"] == "u1"


def test_bad_signature_rejected():
    t = sign({"sub": "u1", "tenant_id": "t1", "exp": int(time.time()) + 100}, "s1")
    with pytest.raises(ValueError):
        verify(t, "s2")


def test_expired_rejected():
    t = sign({"sub": "u1", "tenant_id": "t1", "exp": int(time.time()) - 10}, "s")
    with pytest.raises(ValueError):
        verify(t, "s")


def test_malformed_rejected():
    with pytest.raises(ValueError):
        verify("not-a-jwt", "s")
