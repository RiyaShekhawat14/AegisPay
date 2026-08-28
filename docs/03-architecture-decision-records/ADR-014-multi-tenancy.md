# ADR-014 — Multi-tenancy

## Context
AegisPay is multi-merchant. Must prevent cross-tenant access while keeping ops simple
and migrations tractable.

## Problem
Choose a tenancy isolation model.

## Options
1. Shared DB / shared schema + Row-Level Security.
2. Shared DB / separate schema.
3. Database-per-tenant.

## Decision
**Shared database, shared schema, with Postgres Row-Level Security** + `tenant_id` on
every table, plus app-layer tenant context and migration-safe policies.

## Rationale
- Hard isolation at the DB engine (RLS) without an ops explosion (one backup, one
  migration path, one analytics plane).
- Cheapest to operate at our stage; no per-tenant DB provisioning; single backup/DR.
- RLS read-only on audit_events also enforces append-only.

## Trade-offs
A single-tenant compromise can affect the shared DB (mitigated by RLS + least-privilege
role + app checks). Wide tables need tenant indexes; any cross-tenant query must be
correct by construction.

## Consequences
Every tenant table has RLS; middleware sets `app.tenant_id`; isolation is proven by
tests. Migration is one schema for all tenants.
