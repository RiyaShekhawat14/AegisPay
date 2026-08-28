# ADR-011 — Audit ledger

## Context
Every financial decision must be auditable and tamper-evident; auditors/regulators and
disputes need proof.

## Problem
Design an audit trail that is append-only, tamper-evident, and doesn't invent
unnecessary cryptography.

## Options
1. **Append-only hash-chained log** with a keyed HMAC (event signature) + periodic
   anchor pins; RLS read-only.
2. Rely on DB timestamps / normal logging (can be altered, no integrity).

## Decision
**Append-only, hash-chained audit ledger** with per-event signature and external anchors
(S3 object-lock), stored in `audit_events`. Written in the same transaction as the state
mutation. Read-only RLS; no soft-delete.

## Rationale
- Tamper-evidence without a heavyweight ledger chain: hash chain detects edits; anchor
  pins it externally; HMAC provides non-repudiation with one key.
- Written atomically with state → no "state changed but not audited" gap.

## Trade-offs
Write amplification (an event per action) and chain-verification cost. We keep it cheap
and verifiable.

## Consequences
`audit_events` are also the domain events (same writer). A verifier recomputes the chain.
Do not store secrets/cards.
