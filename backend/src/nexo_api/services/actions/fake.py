"""Ejecutor transaccional fake que conserva el contrato de producción."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from nexo_api.services.orchestration.clock import UuidIdFactory
from nexo_contracts import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ToolCallStatus,
    ToolConfirmation,
    ToolPermissionContext,
    ToolResult,
)

_ids = UuidIdFactory()


class FakeActionExecutor:
    async def execute(
        self,
        action: ActionRequest,
        *,
        identity: ToolPermissionContext | None = None,
        trace_id: str | None = None,
        tenant_id: int | None = None,
        user_id: int | None = None,
    ) -> ActionResult:
        # El doble no revalida permisos, no correlaciona y no persiste la cita.
        del identity, trace_id, tenant_id, user_id
        folio = f"FOLIO-{uuid4().hex[:8].upper()}"
        # Un cuerpo hex crudo produce con frecuencia inaceptable una secuencia de
        # 10+ dígitos, que `nexo_contracts.ids` rechaza como posible PII (mismo
        # motivo por el que `UuidIdFactory` usa base32 para el grafo real).
        tool_call_id = _ids.new_id("tc")
        return ActionResult(
            action_id=action.action_id,
            status=ActionStatus.SUCCEEDED,
            tool_call_id=tool_call_id,
            tool_result=ToolResult(
                tool_call_id=tool_call_id,
                name=action.tool_name,
                status=ToolCallStatus.SUCCEEDED,
                data={"parameters": action.parameters},
                confirmation=ToolConfirmation(identifier=folio, issued_at=datetime.now(UTC)),
                duration_ms=0,
            ),
        )
