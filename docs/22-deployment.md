# 22 — Deployment

## 1. Model

Two deploy units: **control-plane** (FastAPI: API + workers) and **ai-runtime** (FastAPI).
Both as Docker images on ECS Fargate; supported by Terraform (IaC) in
`infrastructure/`. No manual server provisioning.

## 2. Environments

| Env | Cluster | DB | Secrets | Payments | Purpose |
|---|---|---|---|---|---|
| dev | local compose | local | local env | RAZ Test | iterate |
| staging | mini ECS | RDS single/AZ | secrets:staging | RAZ Test | CI/E2E/red-team/chaos |
| production | ECS multi-AZ | RDS multi-AZ + replica | secrets:prod | RAZ Test (challenge) → live gate | real |

## 3. Deployment flow

```
GitHub → build artifacts (immutable, signed) → ECR
  → ECS service deploy (blue/green or canary)
  → health checks → traffic shift → rollback if alarms
```

## 4. Blue/green & canary

- **Blue/green** for the control-plane API: deploy a new task set, run health checks,
  swap target groups; immediate rollback by swapping back. Simpler + safer than in-place.
- **Canary** for the AI runtime (lower risk): shift a small % of traffic; monitor; then
  ramp.
- Feature flags allow disabling risky money-path changes (e.g., a new policy default)
  without a redeploy.

## 5. Migration strategy

- Forward-only migrations, expanding/contracting:
  1. **Expand** (add nullable column / new table) — code still works on old schema.
  2. **Deploy** new code.
  3. **Contract** (drop/backfill) in a later release once the old path is retired.
- No destructive DDL in a single release; no schema change that would break on rollback.
- Migrations run from a controlled job before the new task set becomes healthy;
  rollback on failure.

## 6. Rollback

- **Schema:** code rolls back to the prior task set (compatible via expanding phase).
- **Data/event:** events are append-only; a rollback is a pointer change, not a revert.
- **Service:** ECS blue/green swap.

## 7. Secrets

Injected at runtime from Secrets Manager via IAM role. No secrets baked into images,
env files in Git, or config maps.

## 8. Artifacts

Immutable, versioned (git SHA + build number) images; signed; scanned (see `docs/23`).
Promotion requires the same artifact hash from staging to production (no rebuild).

## 9. Post-deploy verification

- Health checks + ready probes.
- A synthetic traffic probe that exercises the money path (create → authorize →
  payment → a resolved state) in Test Mode.
- Watch money-path metrics/errors for a burn window after deploy.
