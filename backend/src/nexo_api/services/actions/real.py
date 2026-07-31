"""Ejecutor transaccional real sobre el executor de tools del MCP.

Envuelve una ``ActionRequest`` confirmada en una ``ToolCall`` de escritura y la
corre contra el `ToolExecutor` del catálogo. El folio, el flag `is_mock` y el
`provider` los produce el propio executor (`nexo_mcp.execution`): aquí solo se
mapea `ToolResult → ActionResult`.

Un desenlace **desconocido** (p.ej. timeout de escritura) se propaga como
excepción para que la capa HTTP lo registre como `UNKNOWN_OUTCOME` sin
reintentar; un fallo conocido viaja dentro del `ActionResult` como `failed`.
"""

from __future__ import annotations

from nexo_api.services.orchestration.clock import UuidIdFactory
from nexo_contracts import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ToolCall,
    ToolCallStatus,
    ToolMode,
    ToolPermissionContext,
)
from nexo_mcp.catalog import ToolCatalog
from nexo_mcp.execution import ToolExecutor, has_unknown_outcome


class UnknownActionOutcome(Exception):
    """El efecto de la escritura es indeterminado; no se reintenta."""


class RealActionExecutor:
    def __init__(
        self, *, catalog: ToolCatalog, executor: ToolExecutor, ids: UuidIdFactory
    ) -> None:
        self._catalog = catalog
        self._executor = executor
        self._ids = ids

    async def execute(
        self,
        action: ActionRequest,
        *,
        identity: ToolPermissionContext,
        trace_id: str,
    ) -> ActionResult:
        definition = self._catalog.definition(action.tool_name)
        if definition is None:
            # Sin definición no hay tool que ejecutar; se reporta como fallo
            # conocido para que el frontend lo muestre sin reintentar.
            return ActionResult(action_id=action.action_id, status=ActionStatus.FAILED)

        call = ToolCall(
            tool_call_id=self._ids.new_id("tc"),
            name=action.tool_name,
            version=definition.version,
            run_id=action.run_id,
            trace_id=trace_id,
            context=identity,
            parameters=action.parameters,
            action_id=action.action_id,
            idempotency_key=action.idempotency_key,
            confirmed=True,
            mode=ToolMode.WRITE,
        )
        result = await self._executor.execute(call)

        if has_unknown_outcome(result):
            raise UnknownActionOutcome(action.action_id)

        status = (
            ActionStatus.SUCCEEDED
            if result.status is ToolCallStatus.SUCCEEDED
            else ActionStatus.FAILED
        )
        return ActionResult(
            action_id=action.action_id,
            status=status,
            tool_call_id=result.tool_call_id,
            tool_result=result,
            idempotency_replayed=result.idempotency_replayed,
            error=result.error.error if result.error else None,
        )
