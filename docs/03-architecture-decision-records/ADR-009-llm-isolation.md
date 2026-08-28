# ADR-009 — LLM isolation

## Context
The LLM is probabilistic and manipulable and must never touch money, secrets, or PII.
The backend is all Python/FastAPI, so isolation cannot rely on a language split.

## Problem
Guarantee the LLM can propose but never execute/authorize a financial action, and never
see secrets/PII — even inside one language.

## Options
1. **Separate FastAPI service** (`ai_runtime`): its own deploy unit, no DB credentials,
   no Razorpay keys, no money tools; only a scoped internal API that returns a
   validated `CommerceIntent`.
2. Embed LLM calls in the same `control_plane` process.

## Decision
**An isolated FastAPI `ai_runtime` service** as a separate deploy unit, with a **process
and permission boundary**. Same language, different privileges.

## Rationale
- Separation of reasoning vs execution (core principle) is preserved.
- The `ai_runtime` has **no** DB access, **no** money credentials, and only a scoped safe
  tool set exposed to the agent. A compromised/injected LLM can only produce an intent
  the control plane deterministically gates.
- Because it is FastAPI too, the split is now purely about privilege, and developer
  velocity stays high (one framework).

## Trade-offs
A service boundary (network hop, OpenTelemetry propagation, extra deploy). Worth it for
the security invariant; it costs no extra language.

## Consequences
Persistent isolation via IAM roles, separate secret grant (none), and no DB pool. The
`ai_runtime` can only emit intents; the `control_plane` is the only thing that can move
money.
