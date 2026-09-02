"""Transaction Passport router (v1): a human-readable, verifiable receipt for a payment."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.db.models import AuditEvent, Authorization, CartItem
from api.db.repositories import OrderRepo, PaymentRepo
from api.dependencies.auth import CurrentPrincipal
from api.dependencies.db import DbSession
from api.modules.passport.service import build

router = APIRouter(prefix="/v1", tags=["passport"])


async def _authz_by_cart(session, cart_id: uuid.UUID) -> Authorization | None:
    res = await session.execute(
        select(Authorization)
        .where(Authorization.cart_id == cart_id)
        .order_by(Authorization.created_at.desc())
        .limit(1)
    )
    return res.scalars().first()


async def _latest_audit_hash(session, tenant_id: str) -> str:
    res = await session.execute(
        select(AuditEvent)
        .where(AuditEvent.tenant_id == uuid.UUID(tenant_id))
        .order_by(AuditEvent.id.desc())
        .limit(1)
    )
    row = res.scalars().first()
    return row.event_hash if row else ""


@router.get("/passport/{payment_id}")
async def get_passport(
    payment_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal
) -> dict:
    payment = await PaymentRepo(session).get(payment_id)
    if payment is None:
        raise HTTPException(404, "not found")
    order = await OrderRepo(session).get(payment.order_id)
    if order is None:
        raise HTTPException(404, "order not found")
    items = await session.execute(select(CartItem).where(CartItem.cart_id == order.cart_id))
    authz = await _authz_by_cart(session, order.cart_id)
    audit_hash = await _latest_audit_hash(session, principal.tenant_id)

    return build(
        order={
            "id": str(order.id),
            "tenant_id": str(order.tenant_id),
            "agent_id": str(order.agent_id),
            "cart_hash": order.cart_hash,
            "policy_version": order.policy_version,
            "total_minor": order.total_minor,
            "currency": order.currency,
        },
        items=[
            {"product_id": str(i.product_id), "line_total_minor": i.line_total_minor}
            for i in items.scalars().all()
        ],
        authorization={
            "status": authz.status if authz else "NONE",
            "cart_hash": authz.cart_hash if authz else "",
            "risk": authz.risk if authz else None,
        },
        policy={},
        approval=None,
        payment={
            "provider": payment.provider,
            "provider_order_id": payment.provider_order_id,
            "provider_payment_id": payment.provider_payment_id,
        },
        audit={"event_hash": audit_hash},
    )
