"""Garantiza que el contrato commiteado coincide con el OpenAPI generado (§13)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from nexo_api.main import create_app

_CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "openapi" / "v1.yaml"


def _current_spec() -> dict[str, Any]:
    import json

    result: dict[str, Any] = json.loads(json.dumps(create_app().openapi()))
    return result


def test_openapi_contract_has_no_drift() -> None:
    assert _CONTRACT.exists(), "Falta contracts/openapi/v1.yaml; corre scripts/export_openapi.py"
    committed = yaml.safe_load(_CONTRACT.read_text(encoding="utf-8"))
    current = _current_spec()
    assert current == committed, (
        "El OpenAPI cambió respecto al contrato. Corre 'uv run python scripts/export_openapi.py' "
        "y commitea contracts/openapi/v1.yaml."
    )


def test_error_schema_documented() -> None:
    spec = _current_spec()
    assert "ProblemDetail" in spec["components"]["schemas"], (
        "Falta el schema de errores en el contrato"
    )
