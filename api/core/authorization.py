"""Authorization: RBAC (dashboard users) + scoped permissions (agents, ABAC).

Layer order: authentication resolves the Principal -> authorization decides what it may do.
Agents are scoped (allowed_tools + scopes) and can never elevate. The deterministic money
gate (policy/risk/authz) sits separately and is always the final authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# RBAC: role -> permissions (dashboard/merchant operators)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},
    "ops": {"catalog.write", "campaign.write", "approval.review"},
    "policy_admin": {"policy.write"},
    "approver": {"approval.decide"},
    "analyst": {"analytics.read"},
    "member": {"catalog.read"},
}

# Permissions that agents can never hold, no matter their scopes.
FOREVER_FORBIDDEN = {"policy.write", "refund.execute", "payment.execute", "campaign.overbudget"}


@dataclass
class ScopedAgent:
    """ABAC for an agent: bounded by allowed tools and scopes. Cannot self-elevate."""

    agent_id: str
    tenant_id: str
    allowed_tools: set[str] = field(default_factory=set)
    scopes: set[str] = field(default_factory=set)

    def can_access(self, tool: str, scope: str, permission: str) -> bool:
        if permission in FOREVER_FORBIDDEN:
            return False
        if scope not in self.scopes:
            return False
        return tool in self.allowed_tools


def has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms or "*" in perms
