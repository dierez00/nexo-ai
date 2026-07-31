"""Puertos de registro y ejecución de tools (`DIE-F0-021`).

La separación entre registro y ejecución es deliberada: el supervisor filtra la
lista de tools *antes* de mostrarla al modelo, y el executor **revalida** la
autorización en el momento de ejecutar. Ninguna de las dos capas confía en la
otra, y ninguna confía en el agente (`DIE-F2-013`).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nexo_contracts import ToolCall, ToolMetadata, ToolResult


class ToolAuthorizationError(Exception):
    """La invocación no está autorizada para el actor, dominio u operación."""

    def __init__(self, tool_name: str, reason: str) -> None:
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"tool {tool_name!r} denegada: {reason}")


@runtime_checkable
class ToolRegistryPort(Protocol):
    """Catálogo versionado de tools disponibles."""

    async def list_tools(
        self,
        *,
        institution_id: str,
        roles: list[str],
        domain: str | None = None,
    ) -> tuple[ToolMetadata, ...]:
        """Tools visibles para ese actor.

        Filtra por institución, rol, dominio y versión. Deniega por defecto: una
        tool no registrada o sin versión no aparece (`DIE-F0-032`).
        """
        ...

    async def get(self, name: str, version: str) -> ToolMetadata | None:
        """Metadata de una versión exacta; `None` si no está registrada."""
        ...


@runtime_checkable
class ToolExecutorPort(Protocol):
    """Ejecución de una tool ya autorizada."""

    async def execute(self, call: ToolCall) -> ToolResult:
        """Ejecuta la invocación y devuelve siempre un resultado tipado.

        No lanza excepciones de proveedor: los fallos viajan dentro de
        `ToolResult.error` como `NormalizedError`, para que el supervisor decida
        con un código estable. Debe revalidar permisos por su cuenta y honrar la
        idempotencia de las escrituras.
        """
        ...
