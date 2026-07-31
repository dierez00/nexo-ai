"""Catálogo ciudadano v1: allowlist cerrada de componentes (`DIE-F1-100`).

El catálogo se define **en código** y el JSON de `a2ui/catalogs/` se genera
desde aquí, igual que los JSON Schema de `contracts`. Escribirlo a mano crearía
dos fuentes de verdad que se desincronizan, y la primera vez que discrepen el
validador aceptará una superficie que el renderer no sabe pintar.

Un `catalog_id` es **inmutable por versión** (ADR 0006): añadir un componente
exige publicar `v2`. No es rigidez por gusto —es lo que permite que el renderer
de Cris declare qué versión soporta y que el servidor no le mande nunca algo que
no sabe dibujar.

Esta es la instalación **mínima**: los diez componentes que los dos recorridos
del MVP necesitan y ni uno más. Formularios, tablas y superficies
administrativas son Fase 3.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError

from nexo_contracts import (
    A2UI_PROTOCOL_VERSION,
    CatalogDescriptor,
    ComponentDescriptor,
    ConfigurationError,
    NexoModel,
)

CITIZEN_CATALOG_ID = "urn:nexo-ia:a2ui:catalog:citizen:v1"
CITIZEN_CATALOG_VERSION = "1.0.0"

# Ruta relativa a la raíz del repositorio, la misma que declara
# `config/catalogs.yaml`.
CITIZEN_CATALOG_PATH = Path("a2ui/catalogs/citizen/v1/catalog.json")
CITIZEN_FREEZE_PATH = Path("a2ui/catalogs/citizen/v1/freeze.json")


class FrozenCatalogManifest(NexoModel):
    """Huellas que hacen inmutable un catálogo entregado al renderer."""

    schema_version: Literal["1"]
    status: Literal["frozen"]
    frozen_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    protocol_version: Literal["v0.9.1"]
    catalog_id: str
    catalog_version: str
    artifacts: dict[
        str,
        Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")],
    ]


def _component(
    name: str, *, children: bool = False, interactive: bool = False
) -> ComponentDescriptor:
    return ComponentDescriptor(
        name=name,
        schema_ref=f"contracts://a2ui/citizen/v1/{name}.v1",
        allows_children=children,
        is_interactive=interactive,
    )


CITIZEN_CATALOG = CatalogDescriptor(
    catalog_id=CITIZEN_CATALOG_ID,
    version=CITIZEN_CATALOG_VERSION,
    title="Catálogo ciudadano de Nexo IA",
    audience="citizen",
    components=[
        # --- Estructura ---
        _component("Column", children=True),
        _component("Card", children=True),
        # --- Contenido ---
        _component("Text"),
        _component("List"),
        _component("Checklist"),
        _component("StatusBanner"),
        _component("CostSummary"),
        _component("SourceList"),
        # --- Interacción ---
        # Los dos únicos componentes interactivos del catálogo ciudadano. Que
        # sean dos y no diez es deliberado: cada componente interactivo es una
        # superficie de ataque que el validador tiene que cubrir.
        _component("SlotPicker", interactive=True),
        _component("ConfirmButton", interactive=True),
    ],
)

# Propiedades admitidas por componente. Cierra `TD-04` de Fase 0: el contrato
# `A2UIComponent` absorbe cualquier propiedad desconocida porque qué admite cada
# componente lo sabe el catálogo, no el modelo. Aquí está el catálogo.
ALLOWED_PROPERTIES: dict[str, frozenset[str]] = {
    "Column": frozenset({"align", "gap"}),
    "Card": frozenset({"title", "tone"}),
    "Text": frozenset({"text", "variant"}),
    "List": frozenset({"items", "ordered"}),
    "Checklist": frozenset({"title", "items", "progress"}),
    "StatusBanner": frozenset({"title", "message", "tone"}),
    "CostSummary": frozenset({"title", "lines", "total"}),
    "SourceList": frozenset({"title", "sources"}),
    "SlotPicker": frozenset({"title", "slots", "selected"}),
    "ConfirmButton": frozenset({"label", "description"}),
}

# Tonos admitidos donde el componente los acepta. Un tono inventado no rompe
# nada visualmente, pero un `tone: "success"` en una advertencia sí engaña.
ALLOWED_TONES = frozenset({"neutral", "info", "success", "warning", "danger"})


def render_catalog_json(catalog: CatalogDescriptor | None = None) -> str:
    """Artefacto que consume el renderer, con las propiedades permitidas."""
    descriptor = catalog or CITIZEN_CATALOG
    payload = {
        **descriptor.model_dump(mode="json", by_alias=True),
        "allowed_properties": {
            name: sorted(properties) for name, properties in sorted(ALLOWED_PROPERTIES.items())
        },
        "allowed_tones": sorted(ALLOWED_TONES),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def export_catalog(
    root: Path,
    catalog: CatalogDescriptor | None = None,
) -> Path:
    """Escribe el catálogo, salvo que altere el citizen v1 congelado."""
    path = root / CITIZEN_CATALOG_PATH
    payload = render_catalog_json(catalog)
    freeze_path = root / CITIZEN_FREEZE_PATH
    if freeze_path.exists():
        manifest = load_freeze_manifest(root)
        expected = manifest.artifacts.get(CITIZEN_CATALOG_PATH.as_posix())
        actual = _sha256(payload.encode())
        if expected is None or actual != expected:
            raise ConfigurationError(
                str(freeze_path),
                f"artifacts.{CITIZEN_CATALOG_PATH.as_posix()}",
                "citizen v1 está congelado; publique un catalog_id v2 para cambiarlo",
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return path


def load_catalog(root: Path, path: Path | None = None) -> CatalogDescriptor:
    """Carga el catálogo publicado y lo valida contra el contrato."""
    relative = path or CITIZEN_CATALOG_PATH
    if relative == CITIZEN_CATALOG_PATH:
        verify_frozen_catalog(root)
    target = root / relative
    raw = json.loads(target.read_text(encoding="utf-8"))
    # Las claves añadidas para el renderer no forman parte del contrato.
    raw.pop("allowed_properties", None)
    raw.pop("allowed_tones", None)
    return CatalogDescriptor.model_validate(raw)


def load_freeze_manifest(root: Path) -> FrozenCatalogManifest:
    """Carga la decisión de congelación con errores accionables."""
    path = root / CITIZEN_FREEZE_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        manifest = FrozenCatalogManifest.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ConfigurationError(str(path), "<raíz>", str(exc)) from exc
    if (
        manifest.catalog_id != CITIZEN_CATALOG_ID
        or manifest.catalog_version != CITIZEN_CATALOG_VERSION
        or manifest.protocol_version != A2UI_PROTOCOL_VERSION
    ):
        raise ConfigurationError(
            str(path),
            "catalog_id",
            "el manifiesto congelado no coincide con las constantes citizen v1",
        )
    return manifest


def verify_frozen_catalog(root: Path) -> FrozenCatalogManifest:
    """Comprueba que ningún artefacto entregado cambió bajo el mismo ID."""
    manifest = load_freeze_manifest(root)
    resolved_root = root.resolve()
    for relative, expected in manifest.artifacts.items():
        target = (root / relative).resolve()
        if not target.is_relative_to(resolved_root):
            raise ConfigurationError(
                str(root / CITIZEN_FREEZE_PATH),
                f"artifacts.{relative}",
                "la ruta sale de la raíz del repositorio",
            )
        try:
            # Git puede materializar los JSON/JSONL con CRLF en Windows por
            # `core.autocrlf`. Las huellas congeladas se calculan sobre el
            # contenido textual canónico LF, no sobre esa representación local.
            actual = _sha256(target.read_bytes().replace(b"\r\n", b"\n"))
        except OSError as exc:
            raise ConfigurationError(str(target), "<archivo>", str(exc)) from exc
        if actual != expected:
            raise ConfigurationError(
                str(target),
                "sha256",
                ("el artefacto citizen v1 cambió después de congelarse; restáurelo o publique v2"),
            )
    return manifest


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> None:  # pragma: no cover - utilidad de línea de comandos
    root = Path(__file__).resolve().parents[3]
    print(f"catálogo escrito en {export_catalog(root).relative_to(root)}")


if __name__ == "__main__":  # pragma: no cover
    main()
