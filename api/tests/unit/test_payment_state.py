import pytest
from api.modules.payments.state import IllegalTransition, PaymentStatus, transition


def test_unknown_is_first_class():
    # UNKNOWN -> PAID/FAILED is legal (provider truth via webhook or reconciliation)
    transition(PaymentStatus.UNKNOWN, PaymentStatus.PAID)
    transition(PaymentStatus.UNKNOWN, PaymentStatus.FAILED)


def test_never_retry_unknown_backwards():
    # A payment can never go back from PAID/failed to UNKNOWN (no regression)
    with pytest.raises(IllegalTransition):
        transition(PaymentStatus.PAID, PaymentStatus.UNKNOWN)
    with pytest.raises(IllegalTransition):
        transition(PaymentStatus.FAILED, PaymentStatus.UNKNOWN)


def test_terminal_states_have_no_next():
    for s in (PaymentStatus.FAILED, PaymentStatus.REFUNDED):
        with pytest.raises(IllegalTransition):
            transition(s, PaymentStatus.PAID)


def test_happy_path():
    transition(PaymentStatus.CREATED, PaymentStatus.AUTH_PENDING)
    transition(PaymentStatus.AUTH_PENDING, PaymentStatus.PAY_PENDING)
    transition(PaymentStatus.PAY_PENDING, PaymentStatus.PAID)
