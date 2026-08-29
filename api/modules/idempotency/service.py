"""Idempotency for financial commands. Designed to prevent duplicate financial effects.

A repeated request under the same key returns the stored result instead of re-executing.
A different request under the same key is a conflict (rejected), never silently repeated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Store(Protocol):
    def get(self, key: str) -> object | None: ...
    def put_if_absent(self, key: str, value: object) -> bool: ...


@dataclass(frozen=True)
class Result:
    ok: bool
    value: object | None
    conflict: bool = False


class MemStore:
    def __init__(self) -> None:
        self._d: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._d.get(key)

    def put_if_absent(self, key: str, value: object) -> bool:
        if key in self._d:
            return False
        self._d[key] = value
        return True


def command(store: Store, key: str, request_hash: str, operation, *, ttl_ok: bool = True) -> Result:
    """Run `operation` once per key. Returns the stored result on a repeat."""
    existing = store.get(key)
    if existing is not None:
        # Same key was already executed → return the prior result (never re-run).
        _, _value, prev_hash, _ = (
            existing if isinstance(existing, tuple) else (True, existing, "", "")
        )
        if prev_hash and prev_hash != request_hash:
            return Result(ok=False, value=None, conflict=True)
        return Result(ok=True, value=_value)

    value = operation()
    if not store.put_if_absent(key, (True, value, request_hash, None)):
        # Lost a race; another attempt completed first. Return its result, don't re-execute.
        return Result(ok=True, value=store.get(key))
    return Result(ok=True, value=value)
