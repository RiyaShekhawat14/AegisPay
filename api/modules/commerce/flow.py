"""Purchase execution flow (the money path) — orchestrates, never delegates safety.

Ports (injected) keep this pure and testable with fakes:
- PaymentProvider: create_order / reconcile / verify_webhook (async)
- PaymentRepo: save / get current payment state
- IdempotencyStore: dedupe a re-sent command
- Outbox: emit a domain event (transactional outbox)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4


class ProviderError(Exception):
    pass


@dataclass
class Payment:
    id: str
    order_id: str
    amount_minor: int
    currency: str
    provider: str
    provider_order_id: str | None = None
    provider_payment_id: str | None = None
    status: str = "AUTHORIZATION_PENDING"  # matches the payment state machine


@dataclass
class Outcome:
    payment_id: str | None
    status: str
    detail: str = "ok"


class PaymentProvider(Protocol):
    async def create_order(self, *, amount_minor: int, currency: str) -> str: ...
    async def reconcile(
        self, *, order_ref: str, payment_ref: str
    ) -> str: ...  # SUCCESS|FAILED|PENDING
    async def verify_webhook(self, *, body: bytes, signature: str) -> bool: ...


class PaymentRepo(Protocol):
    async def save(self, p: Payment) -> None: ...
    async def get(self, payment_id: str) -> Payment | None: ...


class IdempotencyStore(Protocol):
    def get(self, key: str) -> object | None: ...
    def put(self, key: str, value: object) -> None: ...


class Outbox(Protocol):
    async def emit(self, event_type: str, aggregate_id: str, payload: dict) -> None: ...


class MemRepo:
    def __init__(self) -> None:
        self._d: dict[str, Payment] = {}

    async def save(self, p: Payment) -> None:
        self._d[p.id] = p

    async def get(self, payment_id: str) -> Payment | None:
        return self._d.get(payment_id)


class MemIdem:
    def __init__(self) -> None:
        self._d: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._d.get(key)

    def put(self, key: str, value: object) -> None:
        self._d[key] = value


class MemOutbox:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    async def emit(self, event_type: str, aggregate_id: str, payload: dict) -> None:
        self.events.append((event_type, aggregate_id, payload))


@dataclass
class PurchaseFlow:
    repo: PaymentRepo
    idem: IdempotencyStore = field(default_factory=MemIdem)
    outbox: Outbox = field(default_factory=MemOutbox)
    _seen_webhook: set[str] = field(default_factory=set)

    async def initiate_payment(
        self,
        *,
        order_id: str,
        amount_minor: int,
        currency: str,
        provider: PaymentProvider,
        key: str,
        request_hash: str,
    ) -> Outcome:
        stored = self.idem.get(key)
        if stored is not None:
            assert isinstance(stored, Outcome)
            return stored  # idempotent: never re-execute / never double-charge
        try:
            order_ref = await provider.create_order(amount_minor=amount_minor, currency=currency)
            payment = Payment(
                uuid4().hex,
                order_id,
                amount_minor,
                currency,
                "razorpay",
                provider_order_id=order_ref,
                status="PAYMENT_PENDING",
            )
        except (TimeoutError, ConnectionError, ProviderError):  # provider unavailable -> UNKNOWN
            payment = Payment(
                uuid4().hex, order_id, amount_minor, currency, "razorpay", status="UNKNOWN"
            )
        await self.repo.save(payment)
        outcome = Outcome(payment.id, payment.status)
        self.idem.put(key, outcome)
        await self.outbox.emit("payment.initiated", payment.id, {"status": payment.status})
        return outcome

    async def apply_webhook(
        self, *, provider_event_id: str, body: bytes, signature: str, provider: PaymentProvider
    ) -> str:
        if provider_event_id in self._seen_webhook:
            return "deduped"  # duplicate webhook is a safe no-op
        if not await provider.verify_webhook(body=body, signature=signature):
            return "rejected"
        self._seen_webhook.add(provider_event_id)
        await self.outbox.emit("webhook.verified", provider_event_id, {})
        return "applied"

    async def reconcile(self, *, payment_id: str, provider: PaymentProvider) -> str:
        p = await self.repo.get(payment_id)
        if p is None:
            return "not_found"
        result = await provider.reconcile(
            order_ref=p.provider_order_id or "", payment_ref=payment_id
        )
        status = {"SUCCESS": "PAID", "FAILED": "FAILED", "PENDING": "UNKNOWN"}.get(
            result, "UNKNOWN"
        )
        if status in ("PAID", "FAILED"):
            p.status = status
            await self.repo.save(p)
            await self.outbox.emit("payment.reconciled", payment_id, {"status": status})
        return status
