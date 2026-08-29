"""Shared FastAPI dependencies: authenticated principal + tenant context.

Tenant is derived from the authenticated identity and injected here. Handlers never read
tenant_id from the request body.
"""

from typing import Annotated

from fastapi import Depends

from api.core.security import Principal, resolve_principal

CurrentPrincipal = Annotated[Principal, Depends(resolve_principal)]


def get_tenant_id(principal: CurrentPrincipal) -> str:
    return principal.tenant_id


TenantId = Annotated[str, Depends(get_tenant_id)]
