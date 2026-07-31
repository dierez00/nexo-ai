"""Carga y validación de la configuración al arranque (`DIE-F0-036`).

Una configuración inválida detiene el proceso **antes** de aceptar el primer
run, con ruta, campo y motivo. Arrancar con configuración dudosa y descubrirlo
en el tercer nodo del grafo produce un fallo caro y difícil de atribuir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from nexo_contracts import ConfigurationError, NexoModel
from nexo_contracts.config import (
    CatalogsConfig,
    ModelRouterConfig,
    NexoConfig,
    PermissionsConfig,
    PoliciesConfig,
    ToolRegistryConfig,
)

CONFIG_FILES: dict[str, tuple[str, type[NexoModel]]] = {
    "model_router": ("model_router.yaml", ModelRouterConfig),
    "tool_registry": ("tool_registry.yaml", ToolRegistryConfig),
    "permissions": ("permissions.yaml", PermissionsConfig),
    "catalogs": ("catalogs.yaml", CatalogsConfig),
    "policies": ("policies.yaml", PoliciesConfig),
}

ModelProfile = Literal["offline", "gemini"]

_PROFILE_OVERRIDES: dict[ModelProfile, dict[str, str]] = {
    "offline": {},
    "gemini": {
        "model_router": "model_router.gemini.yaml",
        "policies": "policies.gemini.yaml",
    },
}


def default_config_dir() -> Path:
    """`config/` en la raíz del repositorio."""
    return Path(__file__).resolve().parents[3] / "config"


def _format_location(location: tuple[Any, ...]) -> str:
    """Convierte la `loc` de Pydantic en una ruta legible como `aliases.2.provider_ref`."""
    return ".".join(str(part) for part in location) or "<raíz>"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(str(path), "<archivo>", "el archivo no existe")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(str(path), "<yaml>", f"YAML mal formado: {exc}") from exc
    if raw is None:
        raise ConfigurationError(str(path), "<raíz>", "el archivo está vacío")
    if not isinstance(raw, dict):
        raise ConfigurationError(
            str(path),
            "<raíz>",
            f"se esperaba un mapeo en la raíz y se encontró {type(raw).__name__}",
        )
    return raw


def _validate(path: Path, model: type[NexoModel], raw: dict[str, Any]) -> NexoModel:
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        raise ConfigurationError(
            str(path),
            _format_location(first["loc"]),
            first["msg"],
        ) from exc


def load_config(
    config_dir: Path | None = None,
    *,
    model_profile: ModelProfile = "offline",
) -> NexoConfig:
    """Carga, valida y consolida la configuración.

    Lanza `ConfigurationError` con ruta, campo y motivo ante el primer problema.
    """
    directory = config_dir or default_config_dir()
    overrides = _PROFILE_OVERRIDES[model_profile]
    sections: dict[str, NexoModel] = {}
    for key, (filename, model) in CONFIG_FILES.items():
        filename = overrides.get(key, filename)
        path = directory / filename
        sections[key] = _validate(path, model, _load_yaml(path))

    try:
        return NexoConfig.model_validate(sections)
    except ValidationError as exc:
        first = exc.errors()[0]
        raise ConfigurationError(
            str(directory),
            _format_location(first["loc"]),
            first["msg"],
        ) from exc
