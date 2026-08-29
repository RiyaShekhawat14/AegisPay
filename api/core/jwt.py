"""Minimal JWT (HS256) sign/verify, stdlib-only so it's unit-testable without services.

Used by the auth dependency to resolve an authenticated identity (user/agent) -> a
canonical Principal carrying the tenant. The tenant comes from the token/api-key, never
from the client.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def sign(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    seg = _b64(json.dumps(header).encode()) + "." + _b64(json.dumps(payload).encode())
    sig = hmac.new(secret.encode(), seg.encode(), hashlib.sha256).digest()
    return seg + "." + _b64(sig)


def verify(token: str, secret: str) -> dict:
    """Return the payload if the signature is valid and not expired; else raise ValueError."""
    try:
        head, payload, sig = token.split(".")
        expected = hmac.new(secret.encode(), f"{head}.{payload}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64(expected), sig):
            raise ValueError("bad signature")
        claims = json.loads(_unb64(payload))
        if claims.get("exp", 0) < int(time.time()):
            raise ValueError("token expired")
        return claims
    except ValueError:
        raise
    except Exception as exc:  # malformed
        raise ValueError("malformed token") from exc
