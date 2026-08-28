"""Authentication helpers.

Two authenticator surfaces:
- service/agent API keys (scoped, tenant-bound)
- OIDC bearer tokens for dashboard users

Tenant is resolved HERE from the authenticated identity and injected into the request
context. It is never accepted from the request body.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    subject: str          # agent_id or user_id
    principal_type: str   # AGENT | USER | SERVICE
    tenant_id: str        # derived from auth, never from the client


async def resolve_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    # TODO: verify signature/JWT or API key, then map to a canonical Principal.
    # For the skeleton we derive tenant from the token claim; production verifies it.
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "auth verification pending")
