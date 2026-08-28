# ADR-001 — Go vs Python/FastAPI for the backend

## Context
AegisPay's core handles payments, policy, risk, authorization, webhooks, reconciliation,
and audit — correctness-critical and concurrency-sensitive. The AI/LLM tooling is
Python-native.

## Problem
Choose one backend runtime that is fast to build, good with concurrency, strongly typed,
and lets us keep the whole backend in one language.

## Options
1. **Python + FastAPI** — async (Starlette/uvicorn), Pydantic type validation, single
   language with the AI ecosystem, fastest developer velocity, easy for a small team.
2. **Go** — compiled, excellent concurrent throughput, low memory, single binary, but
   slower to build and splits the stack (core in Go, AI in Python).

## Decision
**Python + FastAPI for the entire backend.**

## Rationale
- One language, one toolchain, one mental model. The AI/LLM layer is Python-native anyway,
  so using FastAPI everywhere removes a language split.
- FastAPI is fully async and easily handles our stated volume (`docs/54`): burst ~20 rps,
  sustained ~5 rps. Pydantic gives strong, validated, typed contracts — exactly what a
  money path wants.
- Developer velocity is the dominant constraint for a small team, and framework/ecosystem
  (SQLAlchemy, psycopg, httpx, Celery/ARQ, OpenTelemetry, testing) is mature.
- Deterministic hot paths (policy, risk) are simple rule evaluation; if profiling later
  shows a bottleneck, we offload to `numpy`/process pools or native code — we do not pay
  the complexity of a second language now.

## Trade-offs
- Python is slower per-core and GIL-bound for pure-CPU work; we mitigate with async I/O,
  process pools where needed, and keeping the money path I/O-bound.
- Higher memory per request than Go; acceptable at our scale.
- FastAPI ships as a container rather than a static binary; we already use Docker.

## Consequences
Whole backend is FastAPI. Frontend is TypeScript. The "AI never reaches money" guarantee
is preserved by **process + permission isolation** (ADR-009), not by a language split.
