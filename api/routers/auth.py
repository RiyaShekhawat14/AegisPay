"""Auth routers (v1): signup + login -> a trusted JWT the control plane accepts."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas.auth import AuthOut, LoginIn, SignupIn
from api.services.auth import login, signup

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
