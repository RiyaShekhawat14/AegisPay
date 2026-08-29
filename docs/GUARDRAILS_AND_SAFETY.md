# Guardrails & Safety
- No LLM reaches a money path (structural forbid-list in the gateway).
- Policy + risk + scoped/expiring authorization gate everything.
- UNKNOWN payments are reconciled, never blindly retried.
- Refunds are capped, single-per-key, and blocked for the AI.
- Cart/price/inventory changes invalidate authorization.
- Tamper-evident audit chain.
Detail: docs/10-policy-engine.md, docs/11-risk-engine.md, docs/12-authorization-model.md, docs/17-transaction-passport.md, docs/07-security-architecture.md.
