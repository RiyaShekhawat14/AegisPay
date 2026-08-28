# ADR-007 — Policy engine architecture

## Context
Money actions must be gated deterministically. The LLM can be manipulated; policies
must be merchant-controlled, versioned, auditable.

## Problem
Design the policy decision mechanism so it is deterministic, reviewable, and immune to
prompt manipulation.

## Options
1. **Deterministic versioned DSL** evaluated over facts; returns ALLOW/DENY/APPROVAL/
   STEPUP; immutable per version.
2. Let the LLM judge policy (e.g., "apply the policy"). Non-deterministic, manipulable.
3. Hardcode rules. Not merchant-configurable; un-auditable changes.

## Decision
**Deterministic versioned policy engine with a typed DSL** (precedence: DENY always
first), immutable versions, rollback by pointer, evaluated over facts. LLM can only
produce an intent; never evaluate/author policy.

## Rationale
- Deterministic → same inputs, same decision; no model nondeterminism on money.
- Immutable + versioned + `policy_version` recorded → auditable & replayable.
- Precedence/deny-first → safe defaults; conflicts resolved, never by majority.

## Trade-offs
DSL limits expressiveness vs free-form scripts; requires intent/rule authoring. It buys
reviewability, determinism, and safety — the whole point.

## Consequences
Policies live in `policies`/`policy_versions`/`policy_rules`; only `policy_admin` users
edit; every evaluation audited; LLM has no policy tool.
