"""Exportador de JSON Schema (`DIE-F0-011`).

Los JSON Schema publicados en `contracts/jsonschema/` y `contracts/events/` son
artefactos derivados. Se regeneran con:

    python -m nexo_contracts.export

Escribirlos a mano crearía exactamente lo que `contracts/README.md` prohíbe:
tipos duplicados manualmente que se desincronizan del modelo real. El comando es
idempotente y los contract tests fallan si el contenido del repositorio ya no
coincide con lo que produciría una regeneración.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import CONTRACTS_SCHEMA_VERSION
from .examples import INVALID_EXAMPLES, VALID_EXAMPLES
from .registry import CONTRACT_REGISTRY, EVENT_CONTRACTS

SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID_PREFIX = "https://nexo.local/contracts"


def repository_root() -> Path:
    """Raíz del repositorio, deducida desde la ubicación de este paquete."""
    return Path(__file__).resolve().parents[3]


def schema_for(name: str) -> dict[str, Any]:
    """JSON Schema de un contrato, con `$id` estable y dialecto explícito."""
    model = CONTRACT_REGISTRY[name]
    schema = model.model_json_schema(by_alias=True, mode="validation")
    return {
        "$schema": SCHEMA_DIALECT,
        "$id": f"{SCHEMA_ID_PREFIX}/{CONTRACTS_SCHEMA_VERSION}/{name}.json",
        "title": model.__name__,
        **schema,
    }


def _render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def target_path(root: Path, name: str) -> Path:
    """Los eventos se publican aparte porque Dani y Cris los consumen por separado."""
    folder = "events" if name in EVENT_CONTRACTS else "jsonschema"
    return root / "contracts" / folder / f"{name}.{CONTRACTS_SCHEMA_VERSION}.json"


def expected_files(root: Path) -> dict[Path, str]:
    """Contenido que debería tener el repositorio: schemas, ejemplos y fixtures."""
    files = {target_path(root, name): _render(schema_for(name)) for name in CONTRACT_REGISTRY}
    files[root / "contracts" / "jsonschema" / "index.json"] = _render(_build_index())
    files.update(_expected_examples(root))
    files.update(_expected_domain_fixtures(root))
    return files


def _expected_examples(root: Path) -> dict[Path, str]:
    """Ejemplos válidos e inválidos de cada contrato, más su manifiesto (`DIE-F0-018`)."""
    examples_root = root / "contracts" / "examples"
    files: dict[Path, str] = {}

    for name, model in VALID_EXAMPLES.items():
        files[examples_root / "valid" / f"{name}.json"] = _render(
            model.model_dump(mode="json", by_alias=True)
        )

    for example in INVALID_EXAMPLES:
        files[examples_root / "invalid" / f"{example.name}.json"] = _render(example.payload)

    manifest = {
        "contracts_schema_version": CONTRACTS_SCHEMA_VERSION,
        "valid": {
            name: {"contract": name, "file": f"valid/{name}.json"}
            for name in sorted(VALID_EXAMPLES)
        },
        "invalid": {
            example.name: {
                "contract": example.contract,
                "file": f"invalid/{example.name}.json",
                "rejected_by": example.rule,
            }
            for example in sorted(INVALID_EXAMPLES, key=lambda item: item.name)
        },
    }
    files[examples_root / "manifest.json"] = _render(manifest)
    return files


# Fixtures compartidos de los dos recorridos MVP (`DIE-F0-029`). Se derivan de los
# mismos ejemplos canónicos para que backend, agentes, MCP, A2UI y frontend
# consuman exactamente los mismos bytes, sin traducción implícita (`DIE-F0-019`).
_DOMAIN_FIXTURES: dict[str, dict[str, str]] = {
    "vehiculos": {
        "cap_veh_01.run_request": "run_request",
        "cap_veh_01.verified_facts": "verified_facts",
        "cap_veh_01.tool_metadata": "tool_metadata",
        "cap_veh_01.action_request": "action_request",
        "cap_veh_01.action_result": "action_result",
        "cap_veh_01.a2ui_surface": "a2ui_surface",
        "cap_veh_01.event_sequence": "event_sequence",
    },
    "ayuntamiento_empresas": {
        "cap_emp_01.estimate": "estimate",
        "cap_emp_01.skill_manifest": "skill_manifest",
    },
}


def _expected_domain_fixtures(root: Path) -> dict[Path, str]:
    files: dict[Path, str] = {}
    for domain, fixtures in _DOMAIN_FIXTURES.items():
        for filename, contract in fixtures.items():
            path = root / "domains" / domain / "fixtures" / f"{filename}.json"
            files[path] = _render(VALID_EXAMPLES[contract].model_dump(mode="json", by_alias=True))
    return files


def _build_index() -> dict[str, Any]:
    return {
        "contracts_schema_version": CONTRACTS_SCHEMA_VERSION,
        "contracts": {
            name: {
                "model": model.__name__,
                "module": model.__module__,
                "schema": f"{'events' if name in EVENT_CONTRACTS else 'jsonschema'}/"
                f"{name}.{CONTRACTS_SCHEMA_VERSION}.json",
                "ref": f"contracts://{name}.{CONTRACTS_SCHEMA_VERSION}",
            }
            for name, model in sorted(CONTRACT_REGISTRY.items())
        },
    }


def export(root: Path | None = None) -> list[Path]:
    """Escribe todos los schemas y devuelve las rutas generadas."""
    root = root or repository_root()
    written: list[Path] = []
    for path, content in expected_files(root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
        written.append(path)
    return sorted(written)


def drift(root: Path | None = None) -> list[Path]:
    """Archivos cuyo contenido en disco ya no coincide con el modelo actual."""
    root = root or repository_root()
    stale: list[Path] = []
    for path, content in expected_files(root).items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(path)
    return sorted(stale)


def main() -> None:
    written = export()
    print(f"{len(written)} artefactos exportados (schemas, ejemplos y fixtures)")


if __name__ == "__main__":
    main()
