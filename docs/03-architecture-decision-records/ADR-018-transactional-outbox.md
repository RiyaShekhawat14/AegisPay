# ADR-018 — Transactional outbox

## Context
The system must emit an event for every state change (which doubles as an audit record),
and consumers are at-least-once. The guarantee must hold even when the state DB commit
and the event-publish are in different systems.

## Problem
Avoid two classic failures: a state change that commits but whose event is never sent
("committed but not emitted"), and an event sent for a change that never committed
("emitted but not committed").

## Options
1. **Transactional outbox**: write the event to an outbox table in the same DB
   transaction as the state change; a relay publishes to the queue; consumers are
   idempotent (dedupe by event id).
2. Publish the event directly after the DB commit. If the publish fails, the event is
   lost; if the commit fails, a spurious event may exist.

## Decision
**Transactional outbox** (an outbox table written atomically with the state, a relay
that publishes to the queue, and idempotent consumers).

## Rationale
- No lost or phantom events; the review of "state changed ⇒ event emitted ⇒ audited"
  is reliable.
- At-least-once delivery is safe because consumers dedupe by `event_id`.
- Auditing is automatic: since domain events are also the audit records, an outbox means
  no state change without an audit record.

## Trade-offs
An extra table + a relay worker (a small, well-understood pattern). There is a tiny
publish delay between commit and queue delivery, which is fine for our workflows.

## Consequences
An `event_outbox` table, a relay task, and idempotent consumers. This is compatible with
SQS (ADR-005) and keeps the event/audit pipeline reliable and replayable.
