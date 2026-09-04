"""Auth service: email/password signup + login issuing a JWT the control plane trusts.

Passwords are hashed (bcrypt). Every user gets a tenant (signup) and the JWT carries the
tenant + role so the middleware/RLS pin the session to the right merchant. No token is ever
accepted from the frontend to derive tenant — identity comes from login only.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import select, text

from api.core.config import get_settings
from api.core.exceptions import AuthenticationError, ConflictError
from api.core.jwt import sign
from api.db.models import Tenant, User
from api.db.session import Session, tenant_session

TOKEN_TTL_MINUTES = 60


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _token(user: User) -> dict:
    exp = datetime.now(UTC) + timedelta(minutes=TOKEN_TTL_MINUTES)
    return {
        "token": sign(
            {
                "sub": str(user.id),
                "type": "USER",
                "tenant_id": str(user.tenant_id or ""),
                "role": user.role,
                "exp": int(exp.timestamp()),
            },
            get_settings().jwt_secret,
        ),
        "role": user.role,
        "tenant_id": str(user.tenant_id or ""),
    }


async def signup(*, email: str, password: str, role: str, merchant_name: str) -> dict:
    email = email.strip().lower()
    async with Session() as s:
        existing = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("email already registered")
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    async with tenant_session(str(tenant_id)) as s:
        s.add(
            Tenant(
                id=tenant_id, slug=f"slug-{tenant_id}", name=merchant_name or email.split("@")[0]
            )
        )
        s.add(
            User(
                id=user_id,
                email=email,
                password_hash=hash_password(password),
                tenant_id=tenant_id,
                role=role,
            )
        )
        await s.flush()  # persist tenant + user before the RLS tenant_users row references them
        await s.execute(
            text("insert into tenant_users (id, tenant_id, user_id, role) values (:i, :t, :u, :r)"),
            {"i": uuid.uuid4(), "t": tenant_id, "u": user_id, "r": role},
        )
    user = User(id=user_id, email=email, tenant_id=tenant_id, role=role)  # token claims
    return _token(user)


async def login(*, email: str, password: str) -> dict:
    email = email.strip().lower()
    async with Session() as s:
        user = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("invalid credentials")
    return _token(user)
