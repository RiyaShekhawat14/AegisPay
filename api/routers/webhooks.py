"""Webhook router (v1). Untrusted: verify the signature, ack (200). No tenant/auth here —
the webhook is provider -> us, and state-apply happens in the tenant-scoped reconciler."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Request

from api.core.config import get_settings
from api.services.webhooks import verify_webhook

router = APIRouter(prefix="/v1", tags=["webhooks"])


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    # Reuse the provider's verification when configured; fall back to our secret so the
    # endpoint is testable offline.
    verified = False
    secret = get_settings().razorpay_webhook_secret
    if secret:
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        verified = hmac.compare_digest(expected, signature)
    else:
        from api.services.payments import get_provider

        verified = await verify_webhook(get_provider(), body=body, signature=signature)
    return {"status": "applied" if verified else "rejected"}
