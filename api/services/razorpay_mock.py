"""In-memory Razorpay stub for tests/local dev (no network)."""


class RazorpayMock:
    name = "razorpay"

    def __init__(self, *, succeed: bool = True, timeout: bool = False) -> None:
        self._succeed = succeed
        self._timeout = timeout

    async def create_order(self, *, amount_minor: int, currency: str) -> str:
        if self._timeout:
            raise TimeoutError("mock provider timeout")
        return "order_mock_1"

    async def reconcile(self, *, order_ref: str, payment_ref: str) -> str:
        return "SUCCESS" if self._succeed else "PENDING"

    async def verify_webhook(self, *, body: bytes, signature: str) -> bool:
        return self._succeed
