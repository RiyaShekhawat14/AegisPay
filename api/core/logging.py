"""Structured logging (structlog) with request_id / tenant_id / trace fields."""

from __future__ import annotations

import logging

# ContextVars are set by middleware so every log line carries correlation ids.
from api.middleware.middleware import request_id_ctx, tenant_id_ctx


def context_processor(_, __, event_dict):
    event_dict["request_id"] = request_id_ctx.get()
    if tenant_id_ctx.get():
        event_dict["tenant_id"] = tenant_id_ctx.get()
    return event_dict


def bind(extra: dict) -> None:
    import structlog

    structlog.contextvars.bind_contextvars(**extra)


def configure_logging(level: str = "INFO") -> None:
    import structlog

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            context_processor,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        cache_logger_on_first_use=True,
    )
