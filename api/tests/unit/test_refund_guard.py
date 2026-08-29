from api.modules.refunds.guard import decide


class Ledger:
    def __init__(self):
        self._s = set()

    def applied(self, key):
        return key in self._s

    def record(self, key):
        self._s.add(key)


def test_refund_capped_to_captured():
    l = Ledger()
    assert (
        decide(
            amount_minor=600,
            captured_minor=500,
            refunded_minor=0,
            requested_by="user:u1",
            ledger=l,
            key="r1",
        ).allowed
        is False
    )


def test_ai_cannot_refund():
    l = Ledger()
    assert (
        decide(
            amount_minor=100,
            captured_minor=500,
            refunded_minor=0,
            requested_by="ai:a1",
            ledger=l,
            key="r2",
        ).allowed
        is False
    )


def test_single_effective_refund_per_key():
    l = Ledger()
    assert (
        decide(
            amount_minor=100,
            captured_minor=500,
            refunded_minor=0,
            requested_by="user:u1",
            ledger=l,
            key="r3",
        ).allowed
        is True
    )
    l.record("r3")
    assert (
        decide(
            amount_minor=100,
            captured_minor=500,
            refunded_minor=0,
            requested_by="user:u1",
            ledger=l,
            key="r3",
        ).allowed
        is False
    )
