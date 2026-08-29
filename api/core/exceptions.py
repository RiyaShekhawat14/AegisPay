"""Standard error model for the API (see docs/45-api-error-catalog.md).

Every error becomes {"code","message","request_id","retryable"}. Handlers map AppError
subclasses to the right HTTP status; the request_id is attached by the request-id middleware.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    code = "INTERNAL_ERROR"
    status = 500
    retryable = False

    def __init__(self, message: str, *, request_id: str = "") -> None:
        self.message = message
        self.request_id = request_id
        super().__init__(message)


class ValidationError(AppError):
    code, status, retryable = "VALIDATION_ERROR", 400, False


class AuthenticationError(AppError):
    code, status, retryable = "AUTHENTICATION_ERROR", 401, False


class AuthorizationError(AppError):
    code, status, retryable = "AUTHORIZATION_ERROR", 403, False


class PolicyDenied(AppError):
    code, status, retryable = "POLICY_DENIED", 403, False


class ConflictError(AppError):
    code, status, retryable = "CONFLICT", 409, False


class ProviderError(AppError):
    code, status, retryable = "PROVIDER_ERROR", 502, True


def error_payload(exc: AppError) -> dict:
    return {
        "code": exc.code,
        "message": exc.message,
        "request_id": exc.request_id,
        "retryable": exc.retryable,
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        if not exc.request_id:
            exc.request_id = (
                request.state.request_id if hasattr(request.state, "request_id") else ""
            )
        return JSONResponse(error_payload(exc), status_code=exc.status)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            {
                "code": "INTERNAL_ERROR",
                "message": "internal error",
                "request_id": getattr(request.state, "request_id", ""),
                "retryable": False,
            },
            status_code=500,
        )
