import pytest

from app.modules.protocol_gateway.canonical import CanonicalIntent
from app.modules.protocol_gateway.gateway import Gateway, MemIdempotency


def _gw():
    return Gateway(
        authenticate=lambda t: t.split(":", 1)[1] if ":" in t else t,
        schema_validator=lambda raw: raw,
        replay_guard=lambda raw: raw.get("nonce") != "old",
        idempotency=MemIdempotency(),
    )


def test_mcp_normalizes_to_non_payment_action():
    intent = _gw().enter(
        "MCP",
        {"tool": "add_to_cart", "product_id": "p1", "qty": 1},
        token="tok:u1",
        merchant_id="m1",
        agent_id="a1",
    )
    assert isinstance(intent, CanonicalIntent)
    assert intent.action == "ADD_TO_CART"


def test_no_adapter_can_produce_payment():
    for proto in ["mcp", "a2a", "acp", "ucp", "ap2", "x402", "upi"]:
        i = _gw().enter(
            proto,
            {"tool": "x", "intent": "checkout", "task": {"kind": "purchase"}},
            token="tok:u1",
            merchant_id="m1",
            agent_id="a1",
        )
        assert i.action != "EXECUTE_PAYMENT"
        assert i.action not in {"ISSUE_REFUND", "MODIFY_ORDER", "UPDATE_POLICY"}


def test_idempotent_replay_returns_same_intent():
    g = _gw()
    a = g.enter(
        "MCP",
        {"tool": "search_catalog"},
        token="tok:u1",
        merchant_id="m1",
        agent_id="a1",
        idempotency_key="k1",
    )
    b = g.enter(
        "MCP",
        {"tool": "search_catalog"},
        token="tok:u1",
        merchant_id="m1",
        agent_id="a1",
        idempotency_key="k1",
    )
    assert a == b


def test_replay_detection_blocks_old_nonce():
    with pytest.raises(ValueError):
        _gw().enter(
            "MCP",
            {"tool": "search_catalog", "nonce": "old"},
            token="tok:u1",
            merchant_id="m1",
            agent_id="a1",
        )


def test_unknown_protocol_rejected():
    with pytest.raises(ValueError):
        _gw().enter("foo", {}, token="tok:u1", merchant_id="m1", agent_id="a1")
