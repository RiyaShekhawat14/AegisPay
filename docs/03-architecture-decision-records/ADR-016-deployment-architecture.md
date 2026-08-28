# ADR-016 — Deployment architecture (ECS vs EKS vs others)

## Context
Deploy a small, mostly stateless set of containers (API + workers + a Python runtime)
plus managed data, on AWS, with a small team.

## Problem
Choose the container orchestrator/threshold.

## Options
1. **ECS (Fargate)** — managed orchestration, no control plane to run, simple tasks,
   cost-efficient, easy multi-AZ.
2. **EKS (Kubernetes)** — richer scheduling, ecosystem, autoscaling, but a control plane
   to operate and more surface.
3. Bare EC2/Compose — too manual.

## Decision
**ECS Fargate** for v1. No Kubernetes.

## Rationale
- Operationally simplest for the real scale (`docs/54`): a few stateless services + a job
  queue need no K8s scheduler features.
- Fargate: no nodes to patch, fine-grained pricing, multi-AZ, IAM/SM/permissions built in.
- Less platform surface → fewer security/ops incidents for a small team.

## Trade-offs
Less portable than EKS (if we need it later); some K8s-native tooling unavailable. K8s
autoscaling/scheduling isn't needed at this scale.

## Consequences
Deploy via ECS blue/green task sets; Terraform IaC; images versioned/scanned; EKS is a
possible later migration if feature needs grow, not a prerequisite.
