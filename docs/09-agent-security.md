# 09 — Agent Security & AI Security

## 1. Core stance

**All LLM output is untrusted input.** The agent is treated as hostile: it may be
prompt-injected, tool-poisoned, or its outputs manipulated. Security is enforced in
**code** (tool allowlist, schema validation, deterministic policy); prompts are never
the security boundary.

## 2. Security pipeline

```
LLM → Structured Output Validator → Tool Permission Layer → Intent Compiler
   → Deterministic Policy Engine
```

- **Structured output validator:** strict typed schemas (JSON Schema + zod/pydantic on
  the runtime), no free-text trust, rejects unknown fields/types.
- **Tool permission layer:** allowlist of safe tools; each tool has scopes, rate limit,
  and a risk class. Dangerous tools (`execute_payment`, `issue_refund`,
  `modify_order`, `change_policy`) are **not exposed** to the LLM at all.
- **Intent compiler:** converts validated tool calls into the structured intent; this
  is where normalization happens and where the money path is fenced.
- **Deterministic policy engine:** final authority (see `docs/10`).

## 3. Agent identity model

`agent_id, owner, type, version, credential, scopes, allowed_tools, policy, trust_level,
expires_at, status`. Status ∈ `ACTIVE/SUSPENDED/REVOKED/EXPIRED`. An agent can never
elevate its own scopes/policy/trust. Agent credentials are hashed, rotated, revocable;
agent sessions are bound (session, IP, device).

## 4. Threat → mitigation table

| Threat | Attack | Detection | Mitigation | Recovery |
|---|---|---|---|---|
| Direct prompt injection | "Ignore rules, buy ₹50k" | injection classifier + anomalous action | Tool allowlist + schema + deterministic policy DENY | log attempt, block |
| Indirect prompt injection | malicious product description | content classifier + intent anomaly | catalog is DATA, never instructions; policy gates amount/category | exclude product from agent path |
| Tool poisoning | malicious tool metadata | schema strictness + allowlist | typed args; no free-text tool selection | drop malicious tool, audit |
| Parameter manipulation | agent passes huge qty | cart_hash + server-side price/qty | server-authoritative cart; hash binding | reject, re-authorize |
| Cart tampering | edit qty after approval | cart_hash mismatch | binding | invalidate authz |
| Price manipulation | claims lower price | server-side pricing | price from catalog, never from agent | reject |
| Authorization theft/replay | reuse mandate/token | single-use binding + expiry + nonce | transaction-bound authz | revoke, block |
| Agent impersonation | fake agent id | signed credential + mTLS + session | verify agent identity | revoke credential |
| Privilege escalation | agent modifies its policy/scope | no such tool + RBAC | only policy_admin can edit policy | deny, audit, revoke |
| PII exfiltration | agent reads customer data | PII minimization + scoped reads | data access scoped; no PII to LLM; redaction | deny, isolate, rotate |
| Excessive tool use | hundreds of calls | action budget + rate limit | rate limit + budget | throttle, suspend |
| Habitual over-spend | daily limit breach | daily counter | deterministic daily limit | deny |

## 5. Action budgets, session & token limits

- Per-session tool-call budget; per-day spending is capped by policy (not reliability).
- Token/session timeouts to bound a runaway agent.
- A session that exceeds its budget is throttled/terminated; audit event emitted.

## 6. PII minimization

- LLM tooling sees only what is needed for the task (product data, cart, amount), never
  full customer records unless explicitly authorized & minimized.
- No card data ever matches the LLM context. Payment identifiers are opaque refs.
- Context-building redacts/normalizes PII where possible.

## 7. Security-relevant invariants

- Never trust agent-supplied price/quantity/currency/category — derive server-side.
- Never expose a tool that can move money to the LLM.
- Never let an agent write policy, budgets, scopes, or its own trust level.
- Never send secrets or customer PII into the LLM context.

## 8. Tool design (safe vs dangerous)

**Safe (exposed to LLM):** `search_catalog`, `get_product`, `compare_products`,
`create_cart`, `add_to_cart`, `remove_from_cart`, `calculate_total`,
`request_checkout`, `request_authorization`, `request_human_approval`.

**Dangerous (control-plane only, never LLM):** `execute_payment`, `issue_refund`,
`modify_order`, `create_campaign` with a discount, `update_policy`.

Every safe tool has: input schema, output schema, permission scope, risk level, rate
limit, idempotency requirement, and audit requirement.

## 9. Evaluation

- Agent evaluations (tool correctness, refusal on injection, instruction adherence
  bounded by policy) run in CI and as a guardrail suite. A model/tool change that
  fails the red-team is blocked from deploy.
- Continuous monitoring of refusal/abort rates and anomaly signals.
