import pytest
from api.modules.commerce.flow import MemIdem, MemOutbox, MemRepo, PurchaseFlow


class FakeProvider:
    def __init__(self):
        self.orders = 0
        self.verified = True

    async def create_order(self, *, amount_minor, currency):
        self.orders += 1
        return "order_1"

    async def reconcile(self, *, order_ref, payment_ref):
        return "SUCCESS"

    async def verify_webhook(self, *, body, signature):
        return self.verified


@pytest.mark.asyncio
async def test_initiate_is_idempotent_no_double_charge():
    repo = MemRepo()
    idem = MemIdem()
    outbox = MemOutbox()
    p = FakeProvider()
    flow = PurchaseFlow(repo, idem, outbox)
    r1 = await flow.initiate_payment(
        order_id="o1", amount_minor=1000, currency="INR", provider=p, key="pk1", request_hash="h1"
    )
    r2 = await flow.initiate_payment(
        order_id="o1", amount_minor=1000, currency="INR", provider=p, key="pk1", request_hash="h1"
    )
    assert r1.payment_id == r2.payment_id
    assert p.orders == 1  # provider called once — no duplicate charge
    assert any(t == "payment.initiated" for t, _, _ in outbox.events)


@pytest.mark.asyncio
async def test_provider_timeout_gives_unknown():
    class TimeoutProvider(FakeProvider):
        async def create_order(self, *, amount_minor, currency):
            raise TimeoutError("provider timeout")

    flow = PurchaseFlow(MemRepo(), MemIdem(), MemOutbox())
    r = await flow.initiate_payment(
        order_id="o1",
        amount_minor=1000,
        currency="INR",
        provider=TimeoutProvider(),
        key="pk2",
        request_hash="h2",
    )
    assert r.status == "UNKNOWN"


@pytest.mark.asyncio
async def test_duplicate_webhook_is_deduped():
    flow = PurchaseFlow(MemRepo(), MemIdem(), MemOutbox())
    p = FakeProvider()
    assert (
        await flow.apply_webhook(provider_event_id="evt1", body=b"{}", signature="s1", provider=p)
        == "applied"
    )
    assert (
        await flow.apply_webhook(provider_event_id="evt1", body=b"{}", signature="s1", provider=p)
        == "deduped"
    )


@pytest.mark.asyncio
async def test_bad_webhook_signature_rejected():
    p = FakeProvider()
    p.verified = False
    flow = PurchaseFlow(MemRepo(), MemIdem(), MemOutbox())
    assert (
        await flow.apply_webhook(provider_event_id="evt2", body=b"{}", signature="bad", provider=p)
        == "rejected"
    )


@pytest.mark.asyncio
async def test_reconcile_resolves_unknown_to_paid():
    repo = MemRepo()
    outbox = MemOutbox()
    idem = MemIdem()
    flow = PurchaseFlow(repo, idem, outbox)
    r = await flow.initiate_payment(
        order_id="o1",
        amount_minor=1000,
        currency="INR",
        provider=FakeProvider(),
        key="pk3",
        request_hash="h3",
    )
    status = await flow.reconcile(payment_id=r.payment_id, provider=FakeProvider())
    assert status == "PAID"
    assert any(t == "payment.reconciled" for t, _, _ in outbox.events)
