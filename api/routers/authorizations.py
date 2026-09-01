"""Authorization + policy routers. The gate: POST evaluate, create, get, approve."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.db.models import Cart
from api.db.repositories import CartRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.modules.authorization.service import AuthorizationService, evaluate
from api.schemas.policy import AuthzApproveIn, AuthzCreateIn, AuthzOut, EvaluateIn, EvaluateOut

router = APIRouter(prefix="/v1", tags=["authorization"])


def _out(authz) -> AuthzOut:
    return AuthzOut(
        id=authz.id,
        cart_id=authz.cart_id,
        cart_hash=authz.cart_hash,
        amount_minor=authz.amount_minor,
        currency=authz.currency,
        status=authz.status,
        policy_version=authz.policy_version,
        risk=authz.risk,
    )


@router.post("/policy/evaluate", response_model=EvaluateOut)
async def eval_policy(
    body: EvaluateIn, session: DbSession, principal: CurrentPrincipal
) -> EvaluateOut:
    ev = evaluate(
        amount_minor=body.amount_minor,
        category=body.category,
        agent_daily_spent_minor=body.agent_daily_spent_minor,
        is_new_buyer=body.is_new_buyer,
        high_velocity=body.high_velocity,
    )
    return EvaluateOut(decision=ev.decision, risk=ev.risk.value, policy_version=ev.policy_version)


@router.post("/authorizations", response_model=AuthzOut, status_code=201)
async def create_authorization(
    body: AuthzCreateIn, session: DbSession, principal: CurrentPrincipal
) -> AuthzOut:
    cart: Cart | None = await CartRepo(session).get(body.cart_id)
    if cart is None:
        raise HTTPException(404, "not found")
    authz = await AuthorizationService(session).create(
        tenant_id=uuid.UUID(principal.tenant_id), cart=cart
    )
    return _out(authz)


@router.get("/authorizations/{authz_id}", response_model=AuthzOut)
async def get_authorization(
    authz_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal
) -> AuthzOut:
    authz = await AuthorizationService(session).get(authz_id)
    if authz is None:
        raise HTTPException(404, "not found")
    return _out(authz)


@router.post("/authorizations/{authz_id}/approve", response_model=AuthzOut)
async def approve_authorization(
    authz_id: uuid.UUID, body: AuthzApproveIn, session: DbSession, principal: CurrentPrincipal
) -> AuthzOut:
    try:
        authz = await AuthorizationService(session).approve(
            authorization_id=authz_id, approver_id=body.approver_id
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return _out(authz)
