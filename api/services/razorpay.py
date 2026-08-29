"""Razorpay provider adapter. Secrets are read here only, never logged.

Implements the provider interface used by the payment flow (create_order / reconcile /
verify_webhook). A provider timeout raises so the flow transitions payment to UNKNOWN.
"""

from __future__ import annotations

import hashlib
import hmac

import httpx

from api.core.config import get_settings


class RazorpayAdapter:
    name = "razorpay"

    def __init__(self) -> None:
        s = get_settings()
        self._key_id = s.razorpay_key_id
        self._secret = s.razorpay_key_secret
        self._base = s.razorpay_base_url
        self._client = httpx.AsyncClient(
            base_url=self._base, auth=(self._key_id, self._secret), timeout=10
        )

    async def create_order(self, *, amount_minor: int, currency: str) -> str:
        r = await self._client.post("/orders", json={"amount": amount_minor, "currency": currency})
        r.raise_for_status()
        return r.json()["id"]

    async def reconcile(self, *, order_ref: str, payment_ref: str) -> str:
        # SUCCESS | FAILED | PENDING (provider truth)
        r = await self._client.get(f"/payments/{payment_ref}")
        r.raise_for_status()
        return {"captured": "SUCCESS", "failed": "FAILED", "authorized": "PENDING"}.get(
            r.json().get("status", "").lower(), "PENDING"
        )

    async def verify_webhook(self, *, body: bytes, signature: str) -> bool:
        expected = hmac.new(self._secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
