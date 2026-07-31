"""Ejecutor transaccional fake (MVP): devuelve un folio simulado."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from nexo_api.services.actions.port import ActionExecution


class FakeActionExecutor:
    async def execute(
        self, action_name: str, action_input: dict[str, Any], tenant_id: int
    ) -> ActionExecution:
        folio = f"FOLIO-{uuid4().hex[:8].upper()}"
        return ActionExecution(
            status="completed",
            folio=folio,
            result_payload={
                "action_name": action_name,
                "echo": action_input,
                "note": "ejecución simulada (MCP transaccional real pendiente)",
            },
        )
