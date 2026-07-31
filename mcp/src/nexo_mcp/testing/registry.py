"""Registry de tools en memoria (`DIE-F0-026`).

Deniega por defecto: una tool no registrada, sin versión, de otra institución o
fuera del rol del actor simplemente no aparece en `list_tools` y no se resuelve
en `get` (`DIE-F0-032`).
"""

from __future__ import annotations

from nexo_contracts import ToolMetadata


class InMemoryToolRegistry:
    """Catálogo de tools versionadas, filtrable por actor y dominio."""

    def __init__(self, tools: list[ToolMetadata] | None = None) -> None:
        self._tools: dict[tuple[str, str], ToolMetadata] = {}
        self._institutions: dict[tuple[str, str], str | None] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolMetadata, *, institution_id: str | None = None) -> None:
        """Registra una versión exacta. `institution_id` nulo significa toda institución."""
        key = (tool.name, tool.version)
        if key in self._tools:
            raise ValueError(
                f"la tool {tool.name!r} versión {tool.version} ya está registrada; "
                f"publicar una versión no reemplaza silenciosamente a otra"
            )
        self._tools[key] = tool
        self._institutions[key] = institution_id

    async def list_tools(
        self,
        *,
        institution_id: str,
        roles: list[str],
        domain: str | None = None,
    ) -> tuple[ToolMetadata, ...]:
        actor_roles = set(roles)
        visible: list[ToolMetadata] = []
        for key, tool in self._tools.items():
            scoped = self._institutions[key]
            if scoped is not None and scoped != institution_id:
                continue
            if domain is not None and tool.domain.value != domain:
                continue
            if not actor_roles & set(tool.allowed_roles):
                continue
            visible.append(tool)
        # Orden estable: la lista que ve el modelo no debe variar entre corridas.
        return tuple(sorted(visible, key=lambda item: (item.name, item.version)))

    async def get(self, name: str, version: str) -> ToolMetadata | None:
        return self._tools.get((name, version))
