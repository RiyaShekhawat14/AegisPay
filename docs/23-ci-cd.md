# 23 — CI/CD

## 1. Pipeline

```
Pull Request
   ↓
Lint (ruff, ESLint, prettier, terraform fmt)
   ↓
Unit Tests (policy/risk/state machine/authorization)
   ↓
Integration Tests (Postgres, Redis, Razorpay Test Mode)
   ↓
Security Scan (SAST: semgrep, bandit; secrets scan: gitleaks)
   ↓
Dependency Scan (pip-audit, npm audit, Dependabot/Renovate)
   ↓
Build (Python wheel, Next.js static)
   ↓
Container Scan (Trivy / Aqua; base-image vulns; sign: cosign)
   ↓
Deploy Staging (blue/green; migrations)
   ↓
E2E Tests (full AI purchase flow + red-team suite)
   ↓
Approval (manual gate if money-path change)
   ↓
Production (canary/blue-green; monitor burn window)
```

## 2. Stages in detail

- **Cache:** accelerate builds with layer caching; pin base images.
- **Red-team** (`docs/38`) runs in staging *before* deploy, as a mandatory gate.
- **Migrations** run safely (expand/contract), gated, reversible.
- **Approval gate** for any diff touching the payment/policy/authorization/audit
  modules (CODEOWNERS).

## 3. Security & dependency

- Review on every PR; fail on critical/high advisories (block).
- Lockfiles committed; pinned base images; SBOM generated (`syft`) per artifact.
- IaC scanned (`checkov`, `tfsec`); drift detection.

## 4. Feature flags & release

- Flags in config; money-path changes shipped dark, enabled via flag, then graduated.
- Trunk-based; short-lived branches; semver tags. Git SHA is the build identifier.

## 5. Rollback

- Blue/green swap; feature-flag revert; forward-only migrations stay compatible.
- Release is a config/artifact promotion, not a code rebuild.

## 6. Environments & promotion

Same immutable artifact promoted dev → staging → production. Staging is the full
gate (integration + red-team + E2E in Test Mode) before production.

## 7. Observability in CI

Coverage thresholds on the safety modules; policy/risk/state-machine tests must pass
and maintain high mutation coverage; a production-readable checklist gate before cut
(`docs/36`).
