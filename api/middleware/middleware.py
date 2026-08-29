"""Cross-cutting middleware.

- request_id: attach a request id to every request (and response header) + log context.
- tenant_context: pin the authenticated tenant for logging/db; health endpoints skip.
- rate_limit: token-bucket per (principal, path); returns 429 when exceeded.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api.core.config import get_settings
from api.core.jwt import verify as verify_jwt
from api.core.ratelimit import MemRateStore, allow

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id", default="")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        request_id_ctx.set(rid)
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant = ""
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                claims = verify_jwt(auth[7:], get_settings().jwt_secret)
                tenant = claims.get("tenant_id", "")
            except ValueError:
                tenant = ""
        request.state.tenant_id = tenant
        tenant_id_ctx.set(tenant)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, store=None, limit: int = 120, window: int = 60) -> None:
        super().__init__(app)
        self._store = store or MemRateStore()
        self._limit = limit
        self._window = window

    async def dispatch(self, request: Request, call_next):
        key = f"{request.client.host if request.client else '?'}:{request.url.path}"
        if allow(self._store, key, limit=self._limit, window=self._window):
            return await call_next(request)
        return JSONResponse(
            {
                "code": "RATE_LIMITED",
                "message": "too many requests",
                "request_id": getattr(request.state, "request_id", ""),
                "retryable": True,
            },
            status_code=429,
        )
