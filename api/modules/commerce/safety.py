"""Commerce safety guards for cart / price / inventory.

Rules:
- prices are server-owned (never from the client)
- a cart hash is a snapshot; any change invalidates the authorization
- a price version change and inventory reservation expiry invalidate the cart
- an authorization is single-use and expiring, and is revalidated before payment
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class CartLine:
    product_id: str
    quantity: int
    unit_price_minor: int  # always server-copied, never client-supplied
    price_version: str


def cart_hash(lines: list[CartLine]) -> str:
    payload = json.dumps(
        [[l.product_id, l.quantity, l.unit_price_minor, l.price_version] for l in lines],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def validate(
    lines: list[CartLine],
    *,
    expected_hash: str,
    price_version: str,
    auth_price_version: str,
    cart_expires_at: str,
    auth_expires_at: str,
    now: str | None = None,
) -> bool:
    """True only if the cart is unchanged, unexpired, and still authorized.

    If price/version/inventory changed, the authorization must be revalidated.
    """
    when = datetime.fromisoformat(now) if now else datetime.now(UTC)
    checks = [
        cart_hash(lines) == expected_hash,
        price_version == auth_price_version,
        datetime.fromisoformat(cart_expires_at) >= when,
        datetime.fromisoformat(auth_expires_at) >= when,
    ]
    return all(checks)
    return True
