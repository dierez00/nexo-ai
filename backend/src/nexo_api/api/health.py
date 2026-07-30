"""Endpoints de salud: liveness y readiness.

- `GET /health/live`  → el proceso responde (no toca dependencias).
- `GET /health/ready` → dependencias mínimas disponibles (hoy: base de datos).
  Migraciones y catálogo mínimo se sumarán cuando Daher entregue el esquema.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from nexo_observability.logging import get_logger
from pydantic import BaseModel

from nexo_api.core.db import check_database

log = get_logger(__name__)
router = APIRouter(tags=["health"])


class LiveResponse(BaseModel):
    status: Literal["alive"] = "alive"


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, str]


@router.get("/health/live", response_model=LiveResponse)
async def live() -> LiveResponse:
    return LiveResponse()


@router.get("/health/ready", response_model=ReadyResponse)
async def ready() -> JSONResponse:
    checks: dict[str, str] = {}
    try:
        await check_database()
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - readiness reporta cualquier fallo
        log.warning("health.ready.database_error", error=str(exc))
        checks["database"] = "error"
        body = ReadyResponse(status="not_ready", checks=checks)
        return JSONResponse(status_code=503, content=body.model_dump())

    body = ReadyResponse(status="ready", checks=checks)
    return JSONResponse(status_code=200, content=body.model_dump())
