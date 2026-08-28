# ADR-002 — Modular Monolith vs Microservices

## Context
The purchase journey is a highly transactional workflow spanning cart → intent →
policy → risk → authorization → payment → webhook → reconcile → audit. It must be
correct and auditable. Team small; time to value matters.

## Problem
Decide deployment granularity: many small services vs one cohesive service with clean
internal modules.

## Options
1. **Microservices** — independent scaling/deploy, but distributed transactions, network
   failure, and operational overhead across the money path.
2. **Modular monolith** — one deploy unit, internal module boundaries, easy transactional
   consistency.

## Decision
**Modular monolith** for the control plane, with one thin separate AI runtime (ADR-009).

## Rationale
- Transactional integrity across cart/order/payment/policy/risk/audit is easiest and
  safest within one process/transaction.
- Faster to build and operate; no distributed-transaction tax on sensitive data.
- Modules are package-bounded (interfaces) so extraction later is cheap.

## Trade-offs
Scales horizontally for stateless API/workers; not per-module scaling for the whole
service. Some vertical-slice boundaries are conceptual, not network.

## Consequences
One FastAPI application (`control_plane/`) with package module boundaries + one separate
FastAPI `ai_runtime/` (ADR-009). If a module becomes hot (e.g., risk), it can be
extracted later without a rewrite.
