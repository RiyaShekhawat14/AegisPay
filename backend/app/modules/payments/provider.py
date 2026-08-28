"""Payment provider abstraction.

No provider concept leaks past this interface. The rest of the codebase sees
PaymentStatus, ProviderOrderID, ProviderPaymentID, amount — never Razorpay/UPI/x402
specifics.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from app.core.config import get_settings


class PaymentProvider(Protocol):
    async def create_order(self, *, amount_minor: int, currency: str) -> ProviderOrder: ...
    async def fetch_payment(self, payment_ref: str) -> ProviderPayment: ...
    async def capture(self, *, payment_ref: str) -> ProviderPayment: ...
    async def refund(self, *, payment_ref: str, amount_minor: int) -> ProviderRefund: ...
    async def verify_webhook(self, *, body: bytes, signature: str) -> bool: ...
    async def reconcile(self, *, order_ref: str, payment_ref: str) -> ProviderPayment: ...


class ProviderOrder:
    def __init__(self, order_ref: str) -> None:
        self.order_ref = order_ref


class ProviderPayment:
    def __init__(self, payment_ref: str, status: str) -> None:
        self.payment_ref = payment_ref
        self.status = status  # SUCCESS | FAILED | PENDING


class ProviderRefund:
    def __init__(self, refund_ref: str) -> None:
        self.refund_ref = refund_ref


class RazorpayAdapter:
    """Razorpay (test mode) adapter. Secrets are read here only, never logged."""

    def __init__(self) -> None:
        self._key_id = get_settings().razorpay_key_id
        self._secret = get_settings().razorpay_key_secret
        self._base = get_settings().razorpay_base_url
        self._client = httpx.AsyncClient(base_url=self._base, auth=(self._key_id, self._secret))

    async def create_order(self, *, amount_minor: int, currency: str) -> ProviderOrder:
        r = await self._client.post("/orders", json={"amount": amount_minor, "currency": currency})
        r.raise_for_status()
        return ProviderOrder(r.json()["id"])

    async def fetch_payment(self, payment_ref: str) -> ProviderPayment:
        r = await self._client.get(f"/payments/{payment_ref}")
        r.raise_for_status()
        return ProviderPayment(payment_ref, r.json()["status"].upper())

    async def capture(self, *, payment_ref: str) -> ProviderPayment:
        return await self.fetch_payment(payment_ref)  # test-mode auto-capture placeholder

    async def refund(self, *, payment_ref: str, amount_minor: int) -> ProviderRefund:
        # TODO: POST /payments/{id}/refund
        raise NotImplementedError

    async def verify_webhook(self, *, body: bytes, signature: str) -> bool:
        import hashlib
        import hmac
        import json

        payload = json.loads(body)
        expected = hmac.new(self._secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return False
        # production: also validate timestamp + event semantics
        return payload.get("account_id") == self._key_id

    async def reconcile(self, *, order_ref: str, payment_ref: str) -> ProviderPayment:
        return await self.fetch_payment(payment_ref)
