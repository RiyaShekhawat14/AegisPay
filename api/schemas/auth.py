"""Auth DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SignupIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role: str = "member"
    merchant_name: str = ""

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        from api.services.auth import validate_password_strength

        validate_password_strength(v)
        return v


class LoginIn(BaseModel):
    email: str
    password: str


class ForgotPasswordIn(BaseModel):
    email: str


class ForgotPasswordOut(BaseModel):
    message: str
    reset_token: str = ""


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        from api.services.auth import validate_password_strength

        validate_password_strength(v)
        return v


class ResetPasswordOut(BaseModel):
    message: str


class AuthOut(BaseModel):
    token: str
    role: str
    tenant_id: str
    agent_id: str = ""
