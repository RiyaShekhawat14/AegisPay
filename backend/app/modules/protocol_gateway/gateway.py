"""Protocol Gateway — the single entry point.

External protocol → authenticate → schema validate → replay protect → idempotency →
Canonical AegisPay Intent → Control Plane.

Gateway never produces a payment execution. Payment is reachable only via the control
plane, after policy/risk/authorization.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from app.modules.protocol_gateway.adapters import ADAPTERS
from app.modules.protocol_gateway.canonical import CanonicalIntent


class IdempotencyStore(Protocol):
    def get(self, key: str) -> object | None: ...
    def put(self, key: str, value: object) -> None: ...


class MemIdempotency:
    def __init__(self) -> None:
        self._d: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._d.get(key)

    def put(self, key: str, value: object) -> None:
        self._d[key] = value


class Gateway:
    def __init__(
        self,
        *,
        authenticate: Callable[[str], str],  # token -> subject (raises on reject)
        schema_validator: Callable[[dict], dict],  # raw -> normalized-safe dict
        replay_guard: Callable[[dict], bool],  # returns False if replay detected
        idempotency: IdempotencyStore | None = None,
    ) -> None:
        self._auth = authenticate
        self._schema = schema_validator
        self._replay = replay_guard
        self._idem = idempotency or MemIdempotency()

    def enter(
        self,
        protocol: str,
        raw: dict,
        *,
        token: str,
        merchant_id: str,
        agent_id: str,
        idempotency_key: str | None = None,
    ) -> CanonicalIntent:
        adapter = ADAPTERS.get(protocol.lower())
        if adapter is None:
            raise ValueError(f"unsupported protocol: {protocol}")
        if idempotency_key and self._idem.get(idempotency_key) is not None:
            # Replay of an already-processed request → return the stored intent (no re-execution).
            stored = self._idem.get(idempotency_key)
            assert isinstance(stored, CanonicalIntent)
            return stored

        subject = self._auth(token)  # authentication
        safe = self._schema(raw)  # schema validation
        if not self._replay(safe):  # replay protection
            raise ValueError("replay detected")
        intent = adapter.normalize(
            safe, agent_id=agent_id, merchant_id=merchant_id, subject=subject
        )
        intent.validate()  # never a payment action
        if idempotency_key:
            self._idem.put(idempotency_key, intent)
        return intent
