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
        tenant_id: int,
        user_id: int | None,
    ) -> ActionResult:
        """Ejecuta una acción ya autorizada sin reinterpretar sus parámetros.

        `identity` y `trace_id` son la identidad efectiva y la traza del run: el
        ejecutor real los propaga a la invocación de la tool para revalidar
        permisos y correlacionar la auditoría. `tenant_id` y `user_id` son las
        claves con las que se persiste el efecto durable de la acción —la cita—;
        `user_id` es `None` para la ciudadanía anónima. Un ejecutor de demo puede
        ignorarlos.
        """
        ...
