"""Protocol Gateway router (v1).

External protocol message -> authenticate -> schema validate -> replay guard ->
CanonicalIntent -> control plane. The gateway never produces a money action; see `canonical`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from api.core.config import get_settings
from api.core.jwt import verify
from api.modules.protocol_gateway.adapters import ADAPTERS
from api.modules.protocol_gateway.canonical import CanonicalIntent
from api.modules.protocol_gateway.gateway import Gateway, MemIdempotency

router = APIRouter(prefix="/v1", tags=["protocol"])

_secret = get_settings().jwt_secret
_gateway = Gateway(
    authenticate=lambda token: verify(token, _secret)["sub"],
    schema_validator=lambda raw: raw,
    replay_guard=lambda _raw: True,
    idempotency=MemIdempotency(),
)


def _bearer(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "authentication required")
    return auth[7:]


@router.post("/protocol/{protocol}")
async def protocol_entry(protocol: str, request: Request) -> dict:
    if protocol.lower() not in ADAPTERS:
        raise HTTPException(400, "unsupported protocol")
    token = _bearer(request)
    try:
        claims = verify(token, _secret)
    except ValueError as exc:
        raise HTTPException(401, "invalid token") from exc
    body = await request.json()
    try:
        intent: CanonicalIntent = _gateway.enter(
            protocol,
            body,
            token=token,
            merchant_id=claims["tenant_id"],
            agent_id=claims["sub"],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "protocol": intent.protocol,
        "agent_id": intent.agent_id,
        "merchant_id": intent.merchant_id,
        "subject": intent.subject,
        "action": intent.action,
        "payload": intent.payload,
    }
