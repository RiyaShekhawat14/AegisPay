"""AegisPay Control Plane — the only component allowed to move money.

FastAPI modular monolith. AuthN/AuthZ, tenant isolation (RLS), rate limiting, structured
logging and tracing/observability are applied centrally; domain services + repositories make
the decisions.
"""

from fastapi import FastAPI

from api.core.exceptions import register_error_handlers
from api.core.logging import configure_logging
from api.core.observability import (
    configure as configure_observability,
)
from api.core.observability import (
    instrument as instrument_observability,
)
from api.middleware.middleware import (
    RateLimitMiddleware,
    RequestIdMiddleware,
    TenantContextMiddleware,
)
from api.routers.router import router

configure_logging()
configure_observability()

app = FastAPI(title="AegisPay Control Plane", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware)
instrument_observability(app)
app.include_router(router)
register_error_handlers(app)
