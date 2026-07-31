"""Puerto de ejecución transaccional de acciones.

La escritura real la hace una tool MCP transaccional (Diego). El backend solo
depende de este Protocol; ver README backend: toda escritura exige permiso,
consentimiento e idempotencia.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class ActionExecution(BaseModel):
    status: str  # completed | failed
    folio: str | None = None
    result_payload: dict[str, Any] = Field(default_factory=dict)


class ActionExecutor(Protocol):
    async def execute(
        self, action_name: str, action_input: dict[str, Any], tenant_id: int
    ) -> ActionExecution: ...
