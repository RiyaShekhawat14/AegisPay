# ADR-008 — Risk engine architecture

## Context
Need an explainable, bounded risk decision. The LLM is probabilistic and manipulable, so
it cannot be the authority.

## Problem
Design risk scoring so it is explainable, layered, and never overridden by a
manipulable model.

## Options
1. **Layered:** deterministic rules + statistical base-rate + optional ML + optional LLM
   qualitative note, where the LLM/ML are weighted but **never** the final authority.
2. Pure ML/LLM risk. Not explainable; single point of failure/manipulation.

## Decision
**Layered fusion with deterministic rules as the hard component**, clamping any model
score; output includes `risk_score, risk_level, risk_factors, recommended_action,
model_version`.

## Rationale
- Deterministic rules always on, never overridden → explainable + robust to prompt
  injection ("LOW risk" from LLM cannot bypass a hard rule).
- `risk_factors` + `model_version` → auditable and explainable.
- Degrade gracefully (rules-only if ML unavailable; fail-closed).

## Trade-offs
More rules to maintain; fusion needs tuning. But it answers "why is risk high" and
resists manipulation.

## Consequences
`risk_assessments` rows; LLM note is explicitly advisory; action is clamped by policy.
