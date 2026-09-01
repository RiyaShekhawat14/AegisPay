"""Authorization: the deterministic gate that binds a cart to a spend decision.

Policy -> Risk -> Authorization. An authorization is single-use and expiring; high-risk
spends require a quorum of approvals before they become VALID. The AI can request one, but
can never grant it — only a human/approver (via approve) can.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import PolicyDenied
from api.db.models import Approval, Authorization, Cart
from api.modules.risk.service import RiskLevel, score
from api.policy.engine import Decision, Facts, Policy, Rule

POLICY_VERSION = "v1"
APPROVAL_TTL_MINUTES = 30
APPROVALS_FOR_RISK = {RiskLevel.HIGH: 2, RiskLevel.MEDIUM: 1, RiskLevel.LOW: 0}


@dataclass(frozen=True)
class Evaluation:
    decision: str
    risk: RiskLevel
    policy_version: str


def default_policy() -> Policy:
    """Merchant-owned default policy: a hard amount cap + a blocked category set."""
    return Policy(
        POLICY_VERSION,
        [
            Rule("amount", "gte", 5_000_000, Decision.DENY, precedence=1),  # hard cap
            Rule("category", "in", ["weapons"], Decision.DENY, precedence=2),
        ],
    )


def evaluate(
    *,
    amount_minor: int,
    category: str = "",
    agent_daily_spent_minor: int = 0,
    is_new_buyer: bool = False,
    high_velocity: bool = False,
) -> Evaluation:
    """Policy -> Risk. DENY always wins; high risk requires human approval."""
    decision, _ = default_policy().evaluate(
        Facts(
            amount_minor=amount_minor,
            category=category,
            hour=datetime.now(UTC).hour,
            agent_daily_spent_minor=agent_daily_spent_minor,
        )
    )
    risk = score(amount_minor=amount_minor, is_new_buyer=is_new_buyer, high_velocity=high_velocity)
    if decision is Decision.DENY:
        return Evaluation("DENY", risk, POLICY_VERSION)
    if risk is RiskLevel.HIGH:
        return Evaluation("HUMAN_APPROVAL_REQUIRED", risk, POLICY_VERSION)
    return Evaluation("ALLOW", risk, POLICY_VERSION)


def required_approvals(risk: RiskLevel) -> int:
    return APPROVALS_FOR_RISK.get(risk, 0)


class AuthorizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        cart: Cart,
        is_new_buyer: bool = False,
        high_velocity: bool = False,
    ) -> Authorization:
        assert cart.cart_hash, "cart must be hashed before authorization"
        ev = evaluate(
            amount_minor=cart.total_minor, is_new_buyer=is_new_buyer, high_velocity=high_velocity
        )
        if ev.decision == "DENY":
            raise PolicyDenied("policy denied")  # policy engine is final
        expires = datetime.now(UTC) + timedelta(minutes=APPROVAL_TTL_MINUTES)
        status = "VALID" if required_approvals(ev.risk) == 0 else "PENDING_APPROVAL"
        authz = Authorization(
            tenant_id=tenant_id,
            agent_id=cart.agent_id,
            cart_id=cart.id,
            cart_hash=cart.cart_hash,
            amount_minor=cart.total_minor,
            currency=cart.currency,
            policy_version=ev.policy_version,
            status=status,
            single_use=True,
            expires_at=expires,
            risk={"risk": ev.risk.value},
        )
        self.session.add(authz)
        await self.session.flush()
        return authz

    async def get(self, authorization_id: uuid.UUID) -> Authorization | None:
        return await self.session.get(Authorization, authorization_id)

    async def approve(
        self, *, authorization_id: uuid.UUID, approver_id: uuid.UUID
    ) -> Authorization:
        authz = await self.session.get(Authorization, authorization_id)
        if authz is None:
            raise ValueError("authorization not found")
        self.session.add(
            Approval(
                tenant_id=authz.tenant_id,
                authorization_id=authz.id,
                approver_id=approver_id,
                decision="APPROVE",
                scope_hash=authz.cart_hash,
                status="APPROVED",
                expires_at=datetime.now(UTC) + timedelta(minutes=APPROVAL_TTL_MINUTES),
            )
        )
        await self.session.flush()
        approved = (
            (
                await self.session.execute(
                    select(Approval).where(
                        Approval.authorization_id == authorization_id,
                        Approval.decision == "APPROVE",
                    )
                )
            )
            .scalars()
            .all()
        )
        risk = RiskLevel((authz.risk or {}).get("risk", "HIGH"))
        if len(approved) >= required_approvals(risk):
            authz.status = "VALID"
            await self.session.flush()
        return authz
