"""AegisPay Control Plane — the only component allowed to move money.

FastAPI modular monolith. AuthN/AuthZ, tenant isolation (RLS), rate limiting, structured
logging and tracing/observability are applied centrally; domain services + repositories make
the decisions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.core.exceptions import register_error_handlers
from api.core.logging import configure_logging
from api.core.observability import (
    configure as configure_observability,
)
from api.core.observability import (
    instrument as instrument_observability,
)
from api.middleware.metrics_middleware import MetricsMiddleware
from api.middleware.middleware import (
    RateLimitMiddleware,
    RequestIdMiddleware,
    TenantContextMiddleware,
)
from api.routers.router import router

configure_logging()
configure_observability()

app = FastAPI(title="AegisPay Control Plane", version="0.1.0")

# Browser origins allowed to call this API (the Next.js frontend). Never trust the frontend
# for identity/tenant — CORS only permits cross-origin requests; auth is still JWT + RLS.
_origins = (
    get_settings().frontend_origins.strip().split(",")
    if get_settings().frontend_origins
    else [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002",
    ]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
instrument_observability(app)
app.include_router(router)
register_error_handlers(app)
