# ADR-012 — Transaction Passport

## Context
Need a single, verifiable record proving what a transaction was, who authorized it,
under which policy/risk, and that the audit chain is intact. Signature feature.

## Problem
Design a provenance bundle that is binding and verifiable without inventing elaborate
crypto.

## Options
1. **Signed/passport field bundle** binding decision-critical hashes (intent, cart,
   authz, policy_version, risk, decision, provider ref) and link to the audit chain;
   display metadata is stored only.
2. Store just an event log without a bound bundle.

## Decision
**Transaction Passport** = a retrievable bundle binding the signed/hashed
decision-critical values into the audit chain; human-readable metadata stored only.

## Rationale
- Binds "what was proposed" = "what was authorized" = "what was executed" → beats
  cart-tampering/replay/substitution.
- No excessive cryptography: salted SHA-256 hashes + the existing HMAC chain signature.
- Explainability + auditability in one object.

## Trade-offs
Some hashing/tooling to generate + verify; maintains an index by transaction id.

## Consequences
`GET /v1/transactions/{id}/passport` returns the bundle; `Audit Integrity: VERIFIED` when
the chain is intact. Produced on every decision path (including DENY).
