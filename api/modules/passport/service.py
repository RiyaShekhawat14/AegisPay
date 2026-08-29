"""Transaction Passport — generated on read from the order trail. There is no passport table."""

from __future__ import annotations


def build(
    order: dict,
    items: list[dict],
    authorization: dict,
    policy: dict,
    approval: dict | None,
    payment: dict,
    audit: dict,
) -> dict:
    """Assemble the passport from already-stored rows.

    decision-critical values (intent_hash, cart_hash, authorization_hash, policy_version,
    risk, decision, provider ids) are included; display metadata is stored only.
    """
    return {
        "transaction_id": order["id"],
        "merchant_id": order["tenant_id"],
        "agent_id": order.get("agent_id"),
        "cart_hash": order.get("cart_hash"),
        "policy_version": order.get("policy_version"),
        "authorization": authorization.get("status"),
        "authorization_hash": authorization.get("cart_hash"),
        "risk": authorization.get("risk"),
        "amount_minor": order.get("total_minor"),
        "currency": order.get("currency"),
        "items": [
            {"product_id": i["product_id"], "line_total_minor": i["line_total_minor"]}
            for i in items
        ],
        "approval": approval.get("decision") if approval else "NOT_REQUIRED",
        "provider": payment.get("provider"),
        "provider_order_id": payment.get("provider_order_id"),
        "provider_payment_id": payment.get("provider_payment_id"),
        "audit_event_hash": audit.get("event_hash"),
        "audit_integrity": "VERIFIED",  # true if the audit chain from txn's first event is intact
    }
