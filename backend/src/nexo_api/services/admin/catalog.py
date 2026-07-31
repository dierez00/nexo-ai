"""Caso de uso: catálogo operativo (DB) y config canónica del sistema.

La config canónica se carga con el loader de `nexo_orchestration` (fuente única);
el catálogo operativo se deriva de la base por tenant.
"""

from __future__ import annotations

from functools import lru_cache

from nexo_api.repositories import catalog as catalog_repo
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.catalog import AdminCatalog, ModuleEntry, PermissionEntry, RoleEntry
from nexo_contracts.config import NexoConfig
from nexo_orchestration.configuration import load_config


@lru_cache(maxsize=1)
def system_config() -> NexoConfig:
    """Config canónica (catalogs, tool_registry, policies, permissions, model_router)."""
    return load_config()


async def get_catalog(user: UserProfile) -> AdminCatalog:
    tenant_id = int(user.tenant_id)
    module_rows = await catalog_repo.modules(tenant_id)
    role_rows = await catalog_repo.roles(tenant_id)
    permission_rows = await catalog_repo.permissions()
    return AdminCatalog(
        modules=[
            ModuleEntry(
                code=r["code"], name=r["name"], is_core=r["is_core"], enabled=bool(r["enabled"])
            )
            for r in module_rows
        ],
        roles=[
            RoleEntry(code=r["code"], name=r["name"], is_system=r["is_system"]) for r in role_rows
        ],
        permissions=[
            PermissionEntry(code=r["code"], module_code=r["module_code"]) for r in permission_rows
        ],
    )
