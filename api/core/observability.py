"""Observability: OpenTelemetry + money-path metrics + tracing middleware.

Wires request/tenant/agent context into spans and exposes the core SLI metrics. Instruments
the FastAPI app; the metrics are scraped by Prometheus/CloudWatch.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.core.config import get_settings
from api.core.logging import request_id_ctx, tenant_id_ctx

try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _OTEL = True
except Exception:  # noqa: BLE001 - OTEL libs optional in dev
    _OTEL = False
    metrics = trace = None

_meter = None
_payment_started: metrics.Counter | None = None
_payment_success: metrics.Counter | None = None


def configure() -> None:
    global _meter, _payment_started, _payment_success
    if not _OTEL:
        return
    resource = Resource.create(
        {"service.name": "aegispay-control", "deployment.environment": get_settings().app_env}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    mp = MeterProvider(resource=resource, metric_readers=[PeriodicExportingMetricReader()])
    metrics.set_meter_provider(mp)
    _meter = metrics.get_meter("aegispay")
    _payment_started = _meter.create_counter("payment_initiated_total", "payment initiation count")
    _payment_success = _meter.create_counter("payment_succeeded_total", "payment success count")


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not _OTEL:
            return await call_next(request)
        tracer = trace.get_tracer("aegispay")
        with tracer.start_as_current_span("http.request") as span:
            span.set_attribute("request_id", request_id_ctx.get())
            span.set_attribute("tenant_id", tenant_id_ctx.get())
            span.set_attribute("http.path", request.url.path)
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            return response


def record_payment(status: str) -> None:
    if _payment_started is not None:
        _payment_started.add(1, {"status": status})
    if status == "PAID" and _payment_success is not None:
        _payment_success.add(1)


def instrument(app: FastAPI) -> None:
    if _OTEL:
        FastAPIInstrumentor.instrument_app(app)
    app.add_middleware(TracingMiddleware)
