"""Exporta el OpenAPI de la app a `contracts/openapi/v1.yaml` (contrato versionado).

Correr tras cualquier cambio de API:
    uv run python scripts/export_openapi.py

El test `test_openapi_no_drift` falla si el archivo commiteado no coincide con
el spec generado (criterio §13: "OpenAPI sin drift").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from nexo_api.main import create_app

_OUTPUT = Path(__file__).resolve().parents[1] / "contracts" / "openapi" / "v1.yaml"


def build_spec() -> dict[str, Any]:
    """Spec normalizado a tipos JSON puros (determinista, sin depender del entorno)."""
    spec: dict[str, Any] = json.loads(json.dumps(create_app().openapi()))
    return spec


def main() -> None:
    spec = build_spec()
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(
        yaml.safe_dump(spec, sort_keys=True, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"OpenAPI exportado -> {_OUTPUT.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
