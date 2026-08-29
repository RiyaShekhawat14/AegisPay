"""Payment state machine. UNKNOWN is first-class and never blindly retried."""

from __future__ import annotations

from enum import Enum


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    AUTH_PENDING = "AUTHORIZATION_PENDING"
    PAY_PENDING = "PAYMENT_PENDING"
    CAPTURED = "CAPTURED"
    PAID = "PAID"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"


ALLOWED: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.CREATED: {PaymentStatus.AUTH_PENDING, PaymentStatus.FAILED},
    PaymentStatus.AUTH_PENDING: {
        PaymentStatus.PAY_PENDING,
        PaymentStatus.FAILED,
        PaymentStatus.UNKNOWN,
    },
    PaymentStatus.PAY_PENDING: {PaymentStatus.PAID, PaymentStatus.FAILED, PaymentStatus.UNKNOWN},
    # UNKNOWN exits only on provider truth (verified webhook / reconciliation)
    PaymentStatus.UNKNOWN: {PaymentStatus.PAID, PaymentStatus.FAILED},
    PaymentStatus.CAPTURED: {PaymentStatus.PAID, PaymentStatus.REFUND_PENDING},
    PaymentStatus.PAID: {PaymentStatus.REFUND_PENDING},
    PaymentStatus.REFUND_PENDING: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: set(),
    PaymentStatus.REFUNDED: set(),
}


class IllegalTransition(ValueError):
    pass


def transition(current: PaymentStatus, next_: PaymentStatus) -> None:
    if next_ not in ALLOWED[current]:
        raise IllegalTransition(f"illegal payment transition {current.value} -> {next_.value}")
