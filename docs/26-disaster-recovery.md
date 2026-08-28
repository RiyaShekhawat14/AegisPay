# 26 — Disaster Recovery

## 1. Honest targets

| Metric | Target | Basis |
|---|---|---|
| RPO | ≤ 15 min | RDS PITR (continuous backups + WAL) — minutes, not hours |
| RTO | ≤ 1 hr | single-region multi-AZ restore + app redeploy in-region |
| Durability | multi-AZ synchronous; PITR for earlier | RDS Multi-AZ + backups |
| Cross-region DR | **Not in v1** | documented, not promised. Cost/volume don't justify yet |
| Restore testing | quarterly | we do not claim recovery we have not tested |

We state achievable targets and explicitly do **not** claim zero-loss or instant
failover.

## 2. Backup strategy

- RDS automated backups (7–35 days) + PITR.
- WAL archiving to S3.
- **Audit ledger** immutability is independent of DB restore (hash chain + anchor to
  S3 + the S3 anchor objects are versioned and WORM-ish). This is a deliberate design
  so a DB restore cannot silently rewrite history.
- S3 versioning + object lock (retain) for raw webhooks, audit anchors, exports.
- Secrets recoverable via Secrets Manager.

## 3. Failure scenarios

| Scenario | Behavior | Recovery |
|---|---|---|
| RDS primary failover | Multi-AZ auto-fails over; fail-closed during the window (no new money) | automatic |
| Region loss (single region) | Not covered in v1; documented | regional restore, RTO >1h, accepted risk |
| Corrupt/lost data | PITR to a point before the incident | restore + run verifier |
| Audit integrity questioned | chain verifier + anchor | restore from immutable root |

## 4. Point-in-time recovery

- Restore to a timestamp before a bad deployment/incident; rerun the verifier to prove
  ledger integrity; replay any post-restore payment events idempotently.

## 5. Restore testing

- Quarterly restore drill in staging: restore the latest backup + PITR, run the audit
  verifier + E2E, record the actual RTO. The `readiness-checklist` gates production on
  a passed drill.

## 6. Data retention

See `docs/33-data-retention.md`. Summary: transactional data as needed; raw webhooks
~90 days; audit ≥ configurable (default 6 years) for regulators — adjust per policy
(reviewed, not asserted); privacy-driven deletion for PII.

## 7. What we do NOT claim

- No multi-region active-active (v1).
- No "instant recovery" (we test and measure RTO).
- No guarantee that every disaster is fully recoverable without the documented
  residual risk (region loss).
