"""Registry de tools construido desde la configuración (`DIE-F1-065`).

El registry es la unión de dos cosas que deben coincidir: las tools **declaradas**
en `config/tool_registry.yaml` y las **implementadas** en
`nexo_mcp.tools.definitions`. Se valida al arranque, y cualquier desajuste entre
las dos detiene el proceso:

- una tool declarada sin implementación no puede invocarse;
- una tool implementada sin declarar no existe para el sistema y sería un
  camino de ejecución que la configuración no gobierna;
- una discrepancia de dominio o de modo entre ambas significa que una de las dos
  miente sobre lo que hace.

Descubrir esto en el tercer nodo de un run sería un fallo caro y difícil de
atribuir; descubrirlo al arrancar es gratis (`DIE-F0-036`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo_contracts import ConfigurationError, ToolMetadata, ToolMode
from nexo_contracts.config import ToolRegistryConfig

from .authorization import PermissionMatrix
from .tools.definitions import DEFINITIONS_BY_NAME, ToolDefinition

CONFIG_PATH = "config/tool_registry.yaml"


@dataclass
class ToolCatalog:
    """Catálogo versionado de tools invocables."""

    config: ToolRegistryConfig
    permissions: PermissionMatrix
    definitions: dict[str, ToolDefinition] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.definitions:
            self.definitions = dict(DEFINITIONS_BY_NAME)
        self._entries = {entry.name: entry for entry in self.config.tools}
        self._validate()

    def _validate(self) -> None:
        declared = set(self._entries)
        implemented = set(self.definitions)

        missing = sorted(declared - implemented)
        if missing:
            raise ConfigurationError(
                CONFIG_PATH,
                "tools",
                f"tools declaradas sin implementación: {missing}; una tool que no se "
                f"puede invocar no debe estar registrada",
            )

        undeclared = sorted(implemented - declared)
        if undeclared:
            raise ConfigurationError(
                CONFIG_PATH,
                "tools",
                f"tools implementadas sin declarar: {undeclared}; sería un camino de "
                f"ejecución que la configuración no gobierna",
            )

        for name, entry in self._entries.items():
            definition = self.definitions[name]
            if entry.version != definition.version:
                raise ConfigurationError(
                    CONFIG_PATH,
                    f"tools.{name}.version",
                    f"la configuración declara {entry.version} y la implementación "
                    f"{definition.version}",
                )
            if entry.domain is not definition.metadata.domain:
                raise ConfigurationError(
                    CONFIG_PATH,
                    f"tools.{name}.domain",
                    f"la configuración declara '{entry.domain.value}' y la implementación "
                    f"'{definition.metadata.domain.value}'",
                )
            if entry.mode is not definition.metadata.mode:
                raise ConfigurationError(
                    CONFIG_PATH,
                    f"tools.{name}.mode",
                    f"la configuración declara '{entry.mode.value}' y la implementación "
                    f"'{definition.metadata.mode.value}'; una de las dos miente sobre si "
                    f"esta tool escribe",
                )

    # -- consulta -----------------------------------------------------------

    def is_enabled(self, name: str) -> bool:
        entry = self._entries.get(name)
        return entry is not None and entry.enabled

    def definition(self, name: str, version: str | None = None) -> ToolDefinition | None:
        """Definición de una tool habilitada, o `None`.

        Una versión distinta de la registrada devuelve `None`: publicar una
        versión no reemplaza silenciosamente a otra.
        """
        definition = self.definitions.get(name)
        if definition is None or not self.is_enabled(name):
            return None
        if version is not None and version != definition.version:
            return None
        return definition

    async def list_tools(
        self, *, institution_id: str, roles: list[str], domain: str | None = None
    ) -> tuple[ToolMetadata, ...]:
        """Tools visibles para un actor (`DIE-F1-066`, `DIE-F2-012`).

        **La lista se filtra antes de mostrársela al modelo.** Un modelo que ve
        una tool que no puede usar acabará proponiéndola, y cada propuesta
        denegada es un turno perdido y una traza más ruidosa.
        """
        visible: list[ToolMetadata] = []
        for name, definition in sorted(self.definitions.items()):
            if not self.is_enabled(name):
                continue
            metadata = definition.metadata
            entry = self._entries[name]
            if entry.institution_id is not None and entry.institution_id != institution_id:
                continue
            if domain is not None and metadata.domain.value != domain:
                continue
            if not set(roles) & set(metadata.allowed_roles):
                continue
            if not self.permissions.visible_modes(
                institution_id=institution_id, roles=roles, tool=metadata
            ):
                continue
            visible.append(metadata)
        return tuple(visible)

    async def get(self, name: str, version: str) -> ToolMetadata | None:
        definition = self.definition(name, version)
        return definition.metadata if definition is not None else None

    def write_tools(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                name
                for name, definition in self.definitions.items()
                if definition.metadata.mode is ToolMode.WRITE
            )
        )
