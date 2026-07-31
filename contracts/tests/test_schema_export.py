"""Los artefactos publicados no se desincronizan del modelo (`DIE-F0-011`).

`contracts/jsonschema/`, `contracts/events/`, `contracts/examples/` y
`domains/*/fixtures/` son derivados. Si alguien cambia un modelo y no regenera,
esta prueba falla indicando exactamente qué archivo quedó viejo.
"""

from __future__ import annotations

import json

import pytest

from nexo_contracts.base import CONTRACTS_SCHEMA_VERSION
from nexo_contracts.export import drift, expected_files, repository_root, schema_for
from nexo_contracts.registry import CONTRACT_REGISTRY

pytestmark = pytest.mark.contract


def test_published_artifacts_match_the_models() -> None:
    stale = drift()
    assert not stale, (
        "hay artefactos desincronizados; ejecuta `python -m nexo_contracts.export`:\n"
        + "\n".join(str(path) for path in stale)
    )


def test_every_contract_produces_a_schema() -> None:
    for name in CONTRACT_REGISTRY:
        schema = schema_for(name)
        assert schema["$id"].endswith(f"/{CONTRACTS_SCHEMA_VERSION}/{name}.json")
        assert schema["$schema"].startswith("https://json-schema.org/")


def test_index_lists_every_published_contract() -> None:
    index_path = repository_root() / "contracts" / "jsonschema" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert set(index["contracts"]) == set(CONTRACT_REGISTRY)
    for name, entry in index["contracts"].items():
        assert entry["ref"] == f"contracts://{name}.{CONTRACTS_SCHEMA_VERSION}"


def test_export_is_idempotent() -> None:
    """Regenerar dos veces produce exactamente el mismo contenido."""
    root = repository_root()
    first = expected_files(root)
    second = expected_files(root)
    assert first == second


def test_events_are_published_separately() -> None:
    """Dani y Cris consumen los eventos aparte del resto de contratos."""
    events_dir = repository_root() / "contracts" / "events"
    published = {path.name for path in events_dir.glob("*.json")}
    assert f"run_event.{CONTRACTS_SCHEMA_VERSION}.json" in published
    assert f"event_sequence.{CONTRACTS_SCHEMA_VERSION}.json" in published
