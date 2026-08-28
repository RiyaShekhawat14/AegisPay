"""Protocol adapters. Each maps an external protocol message to a CanonicalIntent.

Adapters are transport-only: they can never produce a money action. The core never
imports a protocol SDK, and a new protocol is a new adapter over the same contract.
"""

from __future__ import annotations

from typing import Protocol

from app.modules.protocol_gateway.canonical import CanonicalIntent


class ProtocolAdapter(Protocol):
    protocol: str

    def normalize(
        self, raw: dict, *, agent_id: str, merchant_id: str, subject: str
    ) -> CanonicalIntent: ...


class _Base:
    protocol = ""

    def _intent(
        self, action: str, payload: dict, *, agent_id, merchant_id, subject
    ) -> CanonicalIntent:
        return CanonicalIntent(self.protocol, agent_id, merchant_id, subject, action, payload)


class A2AAdapter(_Base):
    """Agent-to-agent task → canonical action."""

    protocol = "A2A"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        kind = raw.get("task", {}).get("kind", "recommend")
        mapping = {"purchase": "REQUEST_AUTH", "search": "DISCOVER", "recommend": "RECOMMEND"}
        return self._intent(
            mapping.get(kind, "RECOMMEND"),
            raw,
            agent_id=agent_id,
            merchant_id=merchant_id,
            subject=subject,
        )


class MCPAdapter(_Base):
    """MCP tool call → canonical action (tool allowlist applied upstream)."""

    protocol = "MCP"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        tool = raw.get("tool", "")
        mapping = {
            "search_catalog": "DISCOVER",
            "get_product": "GET_PRODUCT",
            "add_to_cart": "ADD_TO_CART",
            "request_checkout": "CHECKOUT",
            "request_authorization": "REQUEST_AUTH",
        }
        return self._intent(
            mapping.get(tool, "RECOMMEND"),
            raw,
            agent_id=agent_id,
            merchant_id=merchant_id,
            subject=subject,
        )


class ACPAdapter(_Base):
    protocol = "ACP"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        return self._intent(
            "CHECKOUT" if raw.get("intent") == "checkout" else "RECOMMEND",
            raw,
            agent_id=agent_id,
            merchant_id=merchant_id,
            subject=subject,
        )


class UCPAdapter(_Base):
    protocol = "UCP"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        return self._intent(
            "DISCOVER", raw, agent_id=agent_id, merchant_id=merchant_id, subject=subject
        )


class AP2Adapter(_Base):
    protocol = "AP2"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        # A payment mandate is mapped to REQUEST_AUTH — never to a payment execution.
        return self._intent(
            "REQUEST_AUTH", raw, agent_id=agent_id, merchant_id=merchant_id, subject=subject
        )


class X402Adapter(_Base):
    protocol = "x402"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        return self._intent(
            "GET_PRODUCT", raw, agent_id=agent_id, merchant_id=merchant_id, subject=subject
        )


class UPIAdapter(_Base):
    """NPCI UAP / UPI readiness — watch-list. No compliance claim; maps to a normal action."""

    protocol = "UPI"

    def normalize(self, raw, *, agent_id, merchant_id, subject) -> CanonicalIntent:
        return self._intent(
            "REQUEST_AUTH", raw, agent_id=agent_id, merchant_id=merchant_id, subject=subject
        )


ADAPTERS: dict[str, ProtocolAdapter] = {
    a.protocol.lower(): a
    for a in (
        A2AAdapter(),
        MCPAdapter(),
        ACPAdapter(),
        UCPAdapter(),
        AP2Adapter(),
        X402Adapter(),
        UPIAdapter(),
    )
}
