"""Contratos mínimos de observabilidad operativa."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .primitives import UtcDatetime

CatalogTelemetryState = Literal["no_telemetry", "healthy", "degraded", "down"]


class CatalogEntityTelemetry(NexoModel):
    """Estado observable de una entidad del catálogo durante una ventana temporal."""

    entity_id: str = Field(max_length=200)
    state: CatalogTelemetryState = "no_telemetry"
    window_started_at: UtcDatetime | None = None
    window_ended_at: UtcDatetime | None = None
    last_checked_at: UtcDatetime | None = None

    @model_validator(mode="after")
    def _real_states_require_freshness(self) -> Self:
        if self.state != "no_telemetry" and self.last_checked_at is None:
            raise ValueError(
                "una entidad con estado observable requiere `last_checked_at`; "
                "`no_telemetry` es el único estado permitido sin fuente real"
            )
        if (
            self.window_started_at is not None
            and self.window_ended_at is not None
            and self.window_ended_at < self.window_started_at
        ):
            raise ValueError("la ventana temporal de telemetría está invertida")
        return self


__all__ = ["CatalogEntityTelemetry", "CatalogTelemetryState"]
