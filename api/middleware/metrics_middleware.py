"""Metrics middleware: count HTTP requests by (path, status) for the /metrics scrape."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from api.core.metrics import requests_total


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # group by the route template (path) rather than the raw query string
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path) if route else request.url.path
        requests_total.inc(path, str(response.status_code))
        return response
