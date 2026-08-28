# 00b — GROW / SELL / PROTECT — Product Model & Challenge Interpretation

## 1. Challenge interpretation

The challenge — *AI Growth & Agentic Commerce* — asks us to grow merchant revenue
with AI **and/or** make merchants sellable to AI buyers. It also sets a hard bar:
> *Every money action must be explainable, bounded and gated.* plus show the audit
> trail and demonstrate a failure handled gracefully.

AegisPay interprets the challenge as: **build the layer that makes AI-driven commerce
possible *as a payment platform would want it to be***. That means AI that can create
revenue (GROW), AI that can transact (SELL), and a foundation that makes both safe
(PROTECT). A beautiful growth agent with no financial control is a liability, not a
product; a payment shield with no revenue value is a compliance tool. AegisPay is both.

## 2. The three pillars

### GROW — help merchants increase revenue using AI
- Upsell & cross-sell (affinity-driven, explainable)
- Bundles / offers
- Campaign generation (budget-capped, margin-aware)
- Customer segmentation & re-engagement
- Conversion optimization
- Revenue analytics with honest attribution (AI-generated vs AI-assisted vs organic)

### SELL — make merchants discoverable and transactable by AI buyers
- Agent-readable, machine-readable catalog (DATA separated from INSTRUCTIONS)
- Product discovery, comparison, recommendation
- Conversational checkout
- AI buyer integration (MCP/A2A/x402 over a canonical model)
- End-to-end transaction
- Agent-to-merchant communication

### PROTECT — ensure every AI-driven financial action is safe
- Policy engine (deterministic, versioned)
- Risk engine (explainable, layered)
- Authorization (transaction-bounded)
- Human-in-the-loop (scoped, expiring, non-replayable)
- Transaction Passport (signed provenance)
- Audit trail (append-only, hash-chained, tamper-evident)
- Payment reconciliation (UNKNOWN never blindly retried)
- Prompt-injection defense (LLM is hostile input)
- Agent identity & tool authorization (agents cannot elevate)

## 3. The relationship: PROTECT is the substrate for GROW and SELL

You cannot credibly sell "AI that sells for you" to a merchant or a payment company
unless the money path is safe. So PROTECT is not a bolt-on to GROW/SELL; it is the
**trust substrate** that lets GROW and SELL operate at autonomy levels the merchant
chooses. Every GROW/SELL capability resolves to an intent that passes through the
same deterministic pipeline. That is what makes the whole thing *bounded autonomy* of
the kind a Razorpay engineer would accept.

## 4. Autonomy as a dial, not a binary

Merchants choose autonomy via `merchant_autonomy_level` (L0–L4, `docs/30`). This
directly serves GROW (how much the growth agent may act) and SELL (how much the AI
buyer may transact) while keeping PROTECT intact. Autonomy raises what the agent may
*propose and auto-execute*; it never changes what the control plane may *authorize*.

## 5. Product narrative

> **AegisPay turns an AI agent from a website assistant into a selling channel —
> and it is the only amount of autonomy you trust it with.**

The merchant connects Razorpay Test Mode, imports their catalog, and AegisPay
(c) makes the catalog agent-readable, (b) lets an AI buyer shop it end-to-end, and
(b) uses the same purchase data to grow revenue (affinity, cross-sell, campaigns).
Every one of those actions is explainable, bounded, gated and auditable.

## 6. Where the value is (and is not)

- **Value:** the *combination* of revenue growth + AI transactability + proof that the
  AI could not and did not move money without authorization.
- **Not value:** an AI that looks impressive but can (or might) move money freely;
  or a security system so locked down that no AI can do anything useful.
- **Balance:** autonomy dial + per-action policy + human approval tiers is how you
  keep the AI genuinely useful *and* genuinely safe.

## 7. Metric owners

Measurable outcomes are in `docs/54-success-metrics.md`. GROW owns revenue/uplift and
campaign ROI; SELL owns discovery→checkout→payment success; PROTECT owns safety
(zero unauthorized actions, zero duplicate payments) and operations (latency,
reconciliation success).
