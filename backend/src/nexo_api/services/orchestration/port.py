"""Frontera canónica entre la API y la orquestación."""

from __future__ import annotations

from typing import Protocol

from nexo_contracts import ActionRequest, RunRequest, RunResult
from nexo_orchestration.ports import EventSinkPort


class PendingActionSink(Protocol):
    """Persiste una acción antes de que el cliente pueda confirmarla."""

    async def persist(self, action: ActionRequest, *, tenant_id: int) -> None: ...


class Orchestrator(Protocol):
    async def run(
        self,
        request: RunRequest,
        event_sink: EventSinkPort,
        pending_actions: PendingActionSink,
        *,
        tenant_id: int,
    ) -> RunResult:
        """Ejecuta un run sin depender de modelos locales del backend."""
        ...
