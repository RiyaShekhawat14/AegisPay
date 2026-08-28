# ADR-004 — Redis usage

## Context
Need caching, distributed locks (idempotency/one-active-approval), rate limiting, and
fast reads (catalog, policy eval cache).

## Problem
Decide whether Redis is a source of truth, and how to avoid it becoming one.

## Options
1. Redis as cache/locks/rate only — data always recoverable from PostgreSQL.
2. Redis as a persistent store for some domain state.

## Decision
**Redis is cache/lock/rate only; PostgreSQL is the source of truth.**

## Rationale
- Losing Redis must never cause data loss or inconsistency. By keeping truth in
  PostgreSQL, Redis failure degrades gracefully (fail-closed on money).
- Distributed locks + token-bucket rate limiting are natural Redis uses.

## Trade-offs
Some extra latency in reading canonical data (re-read from Postgres). Must design cache
invalidation carefully.

## Consequences
If Redis is down, rate limiting and caching degrade; the money path still works and
fails closed. Locks use Redis but with a Postgres/DB-backed fallback for correctness of
one-active guarantees.
