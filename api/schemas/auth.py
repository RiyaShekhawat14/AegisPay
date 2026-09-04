"""Auth DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SignupIn(BaseModel):
    email: str
    password: str = Field(min_length=6)
    role: str = "member"
    merchant_name: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class AuthOut(BaseModel):
    token: str
    role: str
    tenant_id: str
