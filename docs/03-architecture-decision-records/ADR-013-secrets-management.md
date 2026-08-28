# ADR-013 — Secrets management

## Context
Razorpay secret, DB credentials, webhook secret, ledger HMAC key, encryption keys. Must
never be in Git/frontend/LLM/logs/plaintext DB.

## Problem
Choose how to store, rotate, and inject secrets.

## Options
1. **AWS Secrets Manager** (managed, rotation, IAM-based access, audit).
2. AWS Parameter Store (cheaper, but fewer rotation/secret features).
3. HashiCorp Vault (great, but another self-managed HA system).
4. Kubernetes Secrets (base64, not encrypted at rest, no rotation).

## Decision
**AWS Secrets Manager** as the primary; KMS for the encryption key; runtime injection
via ECS/IAM. KB-size secrets also supported via Secrets Manager not Parameter Store
(to avoid confusion).

## Rationale
- Managed: rotation, IAM access, audit, automatic secret generation.
- No self-managed Vault HA burden for a small team.
- K8s Secrets (we're on ECS anyway) are permissive.

## Trade-offs
AWS lock-in (fine — we're already AWS), per-secret cost, some latency in reads (mitigate
by caching/one-time fetch at adapter boundary). Never in the app config/image.

## Consequences
Secrets read only where needed (adapter boundary, DB pool init, webhook verify). Rotation
is easy; logging/redaction is a hard rule.
