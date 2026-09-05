"""Auth routers (v1): signup + login -> a trusted JWT the control plane accepts."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas.auth import (
    AuthOut,
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    ResetPasswordIn,
    ResetPasswordOut,
    SignupIn,
)
from api.services.auth import login, request_password_reset, reset_password, signup

router = APIRouter(prefix="/v1", tags=["auth"])


@router.post("/auth/signup", response_model=AuthOut, status_code=201)
async def signup_route(body: SignupIn) -> AuthOut:
    return AuthOut(
        **await signup(
            email=body.email,
            password=body.password,
            role=body.role,
            merchant_name=body.merchant_name,
        )
    )


@router.post("/auth/login", response_model=AuthOut)
async def login_route(body: LoginIn) -> AuthOut:
    return AuthOut(**await login(email=body.email, password=body.password))


@router.post("/auth/forgot-password", response_model=ForgotPasswordOut)
async def forgot_password_route(body: ForgotPasswordIn) -> ForgotPasswordOut:
    return ForgotPasswordOut(**await request_password_reset(email=body.email))


@router.post("/auth/reset-password", response_model=ResetPasswordOut)
async def reset_password_route(body: ResetPasswordIn) -> ResetPasswordOut:
    return ResetPasswordOut(**await reset_password(token=body.token, password=body.password))
