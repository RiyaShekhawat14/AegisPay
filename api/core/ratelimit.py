"""Realtime rate limiting — token bucket (pure, testable). Backed by Redis in production."""

from __future__ import annotations

import time
from typing import Protocol


class RateStore(Protocol):
    def count(self, key: str, window: int) -> int: ...
    def bump(self, key: str, window: int) -> None: ...


class MemRateStore:
    def __init__(self) -> None:
        self._d: dict[str, tuple[int, int]] = {}

    def count(self, key: str, window: int) -> int:
        ts, n = self._d.get(key, (0, 0))
        return n if time.time() - ts < window else 0

    def bump(self, key: str, window: int) -> None:
        ts, n = self._d.get(key, (0, 0))
        self._d[key] = (ts if time.time() - ts < window else time.time(), n + 1)


def allow(store: RateStore, key: str, *, limit: int, window: int) -> bool:
    if store.count(key, window) >= limit:
        return False
    store.bump(key, window)
    return True
