"""Router admin (gated por rol `admin`): métricas, catálogo y config."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from nexo_api.api.deps import require_role
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.catalog import AdminCatalog
from nexo_api.schemas.metric import MetricSet
from nexo_api.services.admin import catalog as catalog_service
from nexo_api.services.admin import metrics as metrics_service
from nexo_contracts.config import NexoConfig

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Singleton de la dependencia de rol (evita llamar require_role en defaults → B008).
_require_admin = require_role("admin")


@router.get(
    "/metrics",
    response_model=MetricSet,
    summary="Métricas operativas del tenant",
    responses=problem_responses(401, 403),
)
async def metrics(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    user: UserProfile = Depends(_require_admin),
) -> MetricSet:
    return await metrics_service.get_metrics(user, from_, to)


@router.get(
    "/catalog",
    response_model=AdminCatalog,
    summary="Catálogo operativo (módulos/roles/permisos del tenant)",
    responses=problem_responses(401, 403),
)
async def catalog(user: UserProfile = Depends(_require_admin)) -> AdminCatalog:
    return await catalog_service.get_catalog(user)


@router.get(
    "/config",
    response_model=NexoConfig,
    summary="Config canónica del sistema (catalogs/tools/policies/permissions)",
    responses=problem_responses(401, 403),
)
async def config(user: UserProfile = Depends(_require_admin)) -> NexoConfig:
    del user  # el gate de rol ya corrió; la config no depende del usuario
    return catalog_service.system_config()
