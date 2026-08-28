# ADR-003 — PostgreSQL architecture

## Context
AegisPay stores merchants, agents, carts, intents, orders, payments, policies, risk,
approvals, campaigns, audit, and webhooks. Money correctness requires ACID.

## Problem
Choose the relational datastore and how it is used (schema, replication, isolation).

## Options
1. PostgreSQL — ACID, JSONB, RLS, PITR, multi-AZ.
2. Another NoSQL/event store for everything (not ACID-friendly, complex OLTP).

## Decision
**PostgreSQL 16 as the transactional source of truth**, with JSONB where a flexible shape
is warranted, RLS for tenancy, and read-replica for analytics.

## Rationale
- Cross-entity integrity (order↔payment↔audit) requires transactions.
- RLS gives per-tenant isolation (ADR-014).
- PITR + multi-AZ gives honest DR.
- JSONB handles policy scopes/tool config/event payloads without schema explosion.

## Trade-offs
Not a pure event-stream store; high-write OLTP. RDBMS scaling is vertical/read-replica.

## Consequences
Schema in `docs/05`; migrations forward-only; analytics on read replicas; money path on
the primary.
