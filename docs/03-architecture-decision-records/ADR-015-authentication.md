# ADR-015 — Authentication

## Context
Multiple principals: merchant dashboard users, server-to-server (merchant/agent
integration), agent protocols, and internal services. Each needs distinct, secure auth.

## Problem
Choose an authentication model across these surfaces.

## Options
1. OIDC/OAuth for users + scoped API keys for server-to-server + mTLS internal +
   OAuth-client-credentials for agent protocols.
2. A single JWT with a coarse user identity, reused everywhere.

## Decision
**Layered authn:** OIDC/OAuth (users, MFA) + scoped, hashed API keys (server integration)
+ OAuth 2.1 client creds for agent protocols + mTLS for internal calls.

## Rationale
- Least privilege: an agent key is *agent-scoped*, not an all-powerful user token.
- Users get MFA + OIDC SSO; integrations get revocable keys; internal mTLS isolates the
  trust domain.
- Agent OAuth subjects map to canonical `agent_id` (identity clarity across protocols).

## Trade-offs
Multiple mechanisms to implement/keep secure; must ensure no downgrade path (e.g.,
agent key can't impersonate a user). RBAC/ABAC sits on top.

## Consequences
One identity resolution layer; tenant derived from auth, never the body; all keys
rotate/hash; internal calls mTLS.
