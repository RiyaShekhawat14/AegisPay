# 21 — Infrastructure (AWS)

## 1. Guiding choices

- **ECS (Fargate) not EKS** for v1 — see ADR-016. Operational simplicity, no control
  plane to run, cheaper for a small team, easy multi-AZ, no K8s complexity for a
  service that mostly needs containers + a job queue.
- **Managed data.** RDS PostgreSQL (primary + multi-AZ + read replica for analytics),
  ElastiCache Redis (cache/locks/rate — never truth), SQS (queue; see ADR-005; Kafka
  only when truly needed).
- **Boring, single-region multi-AZ** first. No multi-region until justified.

## 2. Architecture

```mermaid
flowchart TB
    U[Users / Agents] --> CF[CloudFront + WAF]
    CF --> ALB[ALB]
    ALB --> API[ECS Fargate - control-plane API]
    API --> PGRDS[(RDS PostgreSQL primary)]
    API --> RD[(ElastiCache Redis)]
    API --> SM[(Secrets Manager)]
    API --> SQS[SQS]
    ALB --> AB[ECS Fargate - AI runtime (Python)]
    AB --> LLM[LLM Provider]
    SQS --> WK[ECS Fargate - workers]
    WK --> PGRDS
    WK --> RAZ[Razorpay Test APIs]
    WK --> S3[(S3 - raw webhooks/export)]
    PGRDS --> ROCopy[(RDS read replica - analytics)]
    CM[CloudWatch + OTel] --> AL[Alerts/Dashboards]
```

## 3. Service placement

| Layer | AWS | Notes |
|---|---|---|
| Edge | CloudFront + WAF + Shield | TLS, WAF rules, CDN for dashboard assets |
| API | ALB → ECS Fargate (control-plane API) | private subnets, autoscaling |
| AI runtime | ECS Fargate (Python/FastAPI) | separated compute; no DB creds; outbound LLM via proxy |
| Workers | ECS Fargate (worker task set) | queue-consumers, reconciliation, notifications, analytics |
| Data | RDS PostgreSQL multi-AZ + replica | PITR, RLS, encrypted |
| Cache/locks | ElastiCache Redis | cache, distributed locks, rate limit; never truth |
| Queue | SQS | durable, DLQ; at-least-once |
| Objects | S3 | raw webhooks, audit anchors, exports; versioned, private, encrypted, public-access-blocked |
| Secrets | Secrets Manager | read via IAM role, injected at runtime |
| Observability | CloudWatch + OpenTelemetry | metrics, logs, traces, alarms |

## 4. Environments

### Development
- Local Docker Compose (Postgres, Redis, localstack/SQS, Razorpay Test Mode).
- Fast iterate; no cloud.

### Staging
- Full parity mini-AWS: VPC, single AZ-ish, RDS, Redis, SQS, ECS Fargate, secrets.
- **Razorpay Test Mode** connected; drives E2E + red-team + chaos.
- This is where migrations and deploys are validated.

### Production
- Multi-AZ, more capacity, metrics/alerts, PITR + backups, restricted IAM.
- Razorpay Test Mode initially (challenge scope) with a documented path to live keys
  (still Test/credentialed) and a production-readiness gate (`docs/36`).

## 5. Compute sizing (given traffic assumption in `docs/54`)

Small steady-state: API 2–4 Fargate tasks (~1 vCPU/2GB), workers 2, AI runtime 2.
Autoscale on CPU/queue depth; Redis smallest HA; RDS db.t3.medium (test) →
db.r6g.large (staging), r6g.2xlarge (prod multi-AZ) as measured.

## 6. Networking & security

Private subnets; no public DB/Redis; security groups least-privilege; IAM roles; VPC
endpoints for S3/SQS/Secrets; managed/AWS-managed keys in KMS.

## 7. Trade-offs

- ECS vs EKS: chosen ECS (simplicity, cost, team size). If later we need richer
  scheduling/K8s-native tooling, EKS is a migration, but we start simple (ADR-016).
- SQS vs Kafka: SQS now (durable, simple, integrates with Lambda/Fargate) and an
  event-stream abstraction that lets us move to Kafka or NATS later without rework
  (ADR-005).
