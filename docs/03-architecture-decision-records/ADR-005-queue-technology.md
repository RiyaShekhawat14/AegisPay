# ADR-005 — Queue technology

## Context
Need durable, at-least-once delivery for webhook application, reconciliation, refund,
notifications, analytics, campaign execution. Must isolate poison messages.

## Problem
Choose between a managed queue and a heavier event-stream platform.

## Options
1. **SQS** — durable, simple, DLQ, retry/backoff, integrates with Fargate/lambda.
2. **Kafka/NATS** — event-stream, replay, many consumers, but operational overhead and
   partitioning/schema-management complexity.
3. Just a DB in-tx side effect (no queue) — can't fan-out or retry independently.

## Decision
**SQS** for v1, over an event-bus abstraction.

## Rationale
- Correct/durable with a DLQ; no cluster to run; cheap for our volume (`docs/54`).
- At-least-once + idempotent consumers already account for duplicates.
- The abstraction (an `EventBus` interface) lets us move to Kafka/NATS later if scale
  or replay needs grow.

## Trade-offs
SQS has a retention window and no long replay; ordering is best-effort. Our state
machine + dedupe handle ordering, and we persist raw events for replay.

## Consequences
Workers are idempotent + DLQ-aware. Domain events are also the audit records, so raw
replay is covered by the ledger/S3.
