"""Pydantic request/response DTOs (API contract). Kept thin; domain makes the decisions."""

from __future__ import annotations

from pydantic import BaseModel


class PrincipalOut(BaseModel):
    subject: str
    principal_type: str
    tenant_id: str
    role: str


class ErrorOut(BaseModel):
    code: str
    message: str
    request_id: str = ""
    retryable: bool = False


class Page(BaseModel):
    next_cursor: str | None = None
