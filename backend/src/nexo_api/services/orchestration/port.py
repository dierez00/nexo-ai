"""Puerto de orquestación: contrato que el backend usa para ejecutar un run.

La implementación real la provee Diego (LangGraph). El backend solo depende de
este Protocol; ver `dani-scope` (orquestación como caso de uso in-process).
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from nexo_api.schemas.run import RunRequest, RunStatus


class EmittedEvent(BaseModel):
    """Evento que emite la orquestación; el backend le asigna id/sequence al persistir."""

    type: str
    node_name: str
    data: dict[str, Any] = Field(default_factory=dict)


class OrchestrationResult(BaseModel):
    """Salida de la orquestación (sin tocar la base: eso lo hace el backend)."""

    status: RunStatus
    answer: str
    domain: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    available_actions: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    events: list[EmittedEvent] = Field(default_factory=list)


class Orchestrator(Protocol):
    async def run(self, request: RunRequest) -> OrchestrationResult: ...
