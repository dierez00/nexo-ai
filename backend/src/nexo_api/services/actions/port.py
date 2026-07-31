"""Puerto para ejecutar una ``ActionRequest`` canónica."""

from __future__ import annotations

from typing import Protocol

from nexo_contracts import ActionRequest, ActionResult


class ActionExecutor(Protocol):
    async def execute(self, action: ActionRequest) -> ActionResult:
        """Ejecuta una acción ya autorizada sin reinterpretar sus parámetros."""
        ...
