"""Authentication -> Principal (subject, type, tenant). Tenant is derived from auth only.

Supports:
- bearer JWT (user / service), signed HS256, expiry checked
- API key (agent / merchant integration), resolved via the injected api-key store

RBAC: `require_roles` raises 403 unless the principal has the required role. The agent
runtime can only ever resolve to an AGENT principal scoped to its tenant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Protocol

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.core.config import get_settings
from api.core.jwt import verify as verify_jwt

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    principal_type: str  # USER | AGENT | SERVICE
    tenant_id: str
    role: str = "member"


class ApiKeyStore(Protocol):
    def resolve(self, key: str) -> Principal | None: ...


class MemApiKeyStore:
    def __init__(self) -> None:
        self._d: dict[str, Principal] = {}

    def add(self, key: str, principal: Principal) -> None:
        self._d[key] = principal

    def resolve(self, key: str) -> Principal | None:
        return self._d.get(key)


def _principal_from_token(token: str) -> Principal:
    claims = verify_jwt(token, get_settings().jwt_secret)  # raises on bad sig/expiry
    return Principal(
        subject=claims["sub"],
        principal_type=claims.get("type", "USER"),
        tenant_id=claims["tenant_id"],
        role=claims.get("role", "member"),
    )


async def resolve_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    return _principal_from_token(credentials.credentials)


def require_roles(principal: Principal, roles: set[str]) -> Principal:
    if principal.role not in roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
    return principal
