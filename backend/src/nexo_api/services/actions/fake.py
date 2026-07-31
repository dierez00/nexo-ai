"""Ejecutor transaccional fake que conserva el contrato de producción."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from nexo_contracts import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ToolCallStatus,
    ToolConfirmation,
    ToolPermissionContext,
    ToolResult,
)


class FakeActionExecutor:
    async def execute(
        self,
        action: ActionRequest,
        *,
        identity: ToolPermissionContext | None = None,
        trace_id: str | None = None,
    ) -> ActionResult:
        del identity, trace_id  # el doble no revalida permisos ni correlaciona
        folio = f"FOLIO-{uuid4().hex[:8].upper()}"
        tool_call_id = f"tc_{uuid4().hex}"
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
