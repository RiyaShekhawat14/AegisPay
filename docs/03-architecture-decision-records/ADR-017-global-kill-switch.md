# ADR-017 — Global emergency kill switch

## Context
An AI-driven platform must be able to stop risky money movement the moment something
looks wrong (an attack, a bug, an anomaly surge), without losing the ability to
reconcile, audit, or see what is happening.

## Problem
Provide a single, auditable way to halt new AI-initiated financial actions quickly and
safely.

## Options
1. **Application-level kill switch flag** checked (fast) before any money action, backed
   by Redis for speed and PostgreSQL as the authority.
2. No switch (rely on per-tenant flags / manual per-agent suspension) — slow and scattered.

## Decision
**A global, application-level kill switch** that gates all new money movement
(payment initiation, refund, campaign spend) in one check, with a DB-authoritative and
Redis-cached fast read, audited on every flip, requiring a human + a second role.

## Rationale
- One switch = one place to stop "everything risky" within seconds.
- Fail-closed: if the switch state cannot be read, no new money action proceeds.
- Reads, reconciliation and already-authoritative state continue (an unknown payment is
  still reconciled, not frozen into ambiguity).
- Audited + role-gated so it cannot be flipped by a single compromised account.

## Trade-offs
Adds a fast-check dependency on the money path (mitigated by Redis cache + DB fallback).
The switch is coarse (global), not fine-grained per action — acceptable; per-tenant
controls already exist separately.

## Consequences
A `system.kill_switch` store + gate in the payment/campaign engines; metrics for
"blocked by kill switch"; runbooks for engage/disengage; a top-level test that engaging
it blocks payment initiation and refunds.
