"""Puerto para ejecutar una ``ActionRequest`` canónica."""

from __future__ import annotations

from typing import Protocol

from nexo_contracts import ActionRequest, ActionResult, ToolPermissionContext


class ActionExecutor(Protocol):
    async def execute(
        self,
        action: ActionRequest,
        *,
        identity: ToolPermissionContext,
        trace_id: str,
    ) -> ActionResult:
        """Ejecuta una acción ya autorizada sin reinterpretar sus parámetros.

        `identity` y `trace_id` son la identidad efectiva y la traza del run: el
        ejecutor real los propaga a la invocación de la tool para revalidar
        permisos y correlacionar la auditoría. Un ejecutor de demo puede
        ignorarlos.
        """
        ...
