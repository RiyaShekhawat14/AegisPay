"""Auth service: email/password signup + login issuing a JWT the control plane trusts.

Passwords are hashed (bcrypt). Every user gets a tenant (signup) and the JWT carries the
tenant + role so the middleware/RLS pin the session to the right merchant. No token is ever
accepted from the frontend to derive tenant — identity comes from login only.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import select, text

from api.core.config import get_settings
from api.core.exceptions import AuthenticationError, ConflictError, ValidationError
from api.core.jwt import sign
from api.db.models import Agent, PasswordResetToken, Product, Tenant, User
from api.db.session import Session, tenant_session

TOKEN_TTL_MINUTES = 60
RESET_TOKEN_BYTES = 32
_RESET_LETTER_DIGIT = re.compile(r"(?=.*[A-Za-z])(?=.*\d)")

# Demo catalog seeded into each new tenant so a fresh buyer immediately sees products with
# images (the merchant can replace/augment these via the console). Images are stable
# placeholder photos keyed by SKU.
# Demo catalog seeded into each new tenant so a fresh buyer immediately sees products with
# images (the merchant can replace/augment these via the console). Prices are realistic INR.
_DEMO_PRODUCTS = [
    ("RS-BLK-42", "Runner Pro 42", "shoes/running", 249900, "https://picsum.photos/seed/runner42/400/300"),
    ("SR-WHT-40", "Street Run 40", "shoes/running", 199900, "https://picsum.photos/seed/street40/400/300"),
    ("CT-ACE-01", "Court Ace Tennis", "shoes/tennis", 219900, "https://picsum.photos/seed/courtace/400/300"),
    ("TR-GLD-05", "Trail Blaze 5", "shoes/trail", 299900, "https://picsum.photos/seed/trailblaze/400/300"),
    ("CW-LT-01", "Cloud Walker", "shoes/walking", 159900, "https://picsum.photos/seed/cloudwalker/400/300"),
    ("SK-3PK-01", "Run Sock 3-pack", "apparel/socks", 29900, "https://picsum.photos/seed/socks3pk/400/300"),
    ("TS-CLS-01", "T-Shirt Classic", "apparel", 49900, "https://picsum.photos/seed/tshirt01/400/300"),
    ("BT-SPT-01", "Sport Bottle", "gear/bottles", 39900, "https://picsum.photos/seed/bottle01/400/300"),
    ("CN-MED-01", "Canvas Messenger", "bags", 119900, "https://picsum.photos/seed/messenger01/400/300"),
    ("ST-ECO-01", "Eco Sticker Pack", "accessories", 9900, "https://picsum.photos/seed/sticker01/400/300"),
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _token(user: User, agent_id: str | None = None) -> dict:
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
        "agent_id": agent_id or "",
    }


async def signup(*, email: str, password: str, role: str, merchant_name: str) -> dict:
    email = email.strip().lower()
    async with Session() as s:
        existing = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("email already registered")
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    agent_id = uuid.uuid4()
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
        await s.flush()  # persist tenant + user before the RLS rows below reference them
        await s.execute(
            text("insert into tenant_users (id, tenant_id, user_id, role) values (:i, :t, :u, :r)"),
            {"i": uuid.uuid4(), "t": tenant_id, "u": user_id, "r": role},
        )
        # Every tenant gets a default agent so GROW (campaigns/opportunities) and SELL (carts)
        # can run, plus a small demo catalog with images so a fresh buyer can shop immediately.
        s.add(Agent(id=agent_id, tenant_id=tenant_id, name="shopping-agent", type="SELL"))
        for sku, name, category, price, image_url in _DEMO_PRODUCTS:
            s.add(
                Product(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    sku=sku,
                    name=name,
                    category=category,
                    price_minor=price,
                    image_url=image_url,
                )
            )
    user = User(id=user_id, email=email, tenant_id=tenant_id, role=role)  # token claims
    return _token(user, agent_id=str(agent_id))


async def login(*, email: str, password: str) -> dict:
    email = email.strip().lower()
    async with Session() as s:
        user = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("invalid credentials")
    # Supply the tenant's primary agent id so the frontend can drive GROW/SELL (the agents
    # table is RLS-scoped, so pin the tenant to read it). Empty when the user has no tenant.
    agent_id = ""
    if user.tenant_id is not None:
        async with tenant_session(str(user.tenant_id)) as s:
            agent = (
                await s.execute(
                    select(Agent)
                    .where(Agent.status == "ACTIVE")
                    .order_by(Agent.created_at.asc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            agent_id = str(agent.id) if agent is not None else ""
    return _token(user, agent_id=agent_id)


def validate_password_strength(password: str) -> None:
    """Reject weak passwords: min 8 chars and at least one letter + one digit."""
    if len(password) < 8:
        raise ValidationError("password must be at least 8 characters")
    if not _RESET_LETTER_DIGIT.search(password):
        raise ValidationError("password must contain at least one letter and one digit")


def _reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def request_password_reset(*, email: str) -> dict:
    """Generate a single-use, expiring reset token for the account (if it exists).

    We never reveal whether an account exists (anti-enumeration): a real reset link would be
    emailed. With no mailer configured, the token is returned only when configured to do so
    (dev/demo). The response message is identical whether or not the account exists.
    """
    email = email.strip().lower()
    async with Session() as s:
        user = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
        raw = secrets.token_urlsafe(RESET_TOKEN_BYTES)
        if user is not None:
            s.add(
                PasswordResetToken(
                    user_id=user.id,
                    token_hash=_reset_token_hash(raw),
                    expires_at=datetime.now(UTC)
                    + timedelta(minutes=get_settings().password_reset_ttl_minutes),
                )
            )
            await s.commit()
    settings = get_settings()
    return {
        "message": "If an account exists for that email, a reset link has been sent.",
        # Only return a usable token for a real account, and only outside production.
        "reset_token": raw if (user is not None and settings.password_reset_reveal_token) else "",
    }


async def reset_password(*, token: str, password: str) -> dict:
    """Validate a reset token and set a new password (single-use, expires after TTL)."""
    validate_password_strength(password)
    if not token:
        raise AuthenticationError("invalid or expired reset token")
    token_hash = _reset_token_hash(token)
    async with Session() as s:
        record = (
            await s.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.used_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if record is None or record.expires_at < datetime.now(UTC):
            raise AuthenticationError("invalid or expired reset token")
        user = (await s.execute(select(User).where(User.id == record.user_id))).scalar_one_or_none()
        if user is None:
            raise AuthenticationError("invalid or expired reset token")
        # Burn this token first (a same token cannot be replayed even if the set below fails).
        record.used_at = datetime.now(UTC)
        user.password_hash = hash_password(password)
        await s.commit()
    return {"message": "Password updated."}
