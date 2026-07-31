"""Ejemplos válidos e inválidos de cada contrato (`DIE-F0-018`, §7.8).

El valor de los inválidos está en el mensaje: un contrato que rechaza sin
explicar obliga a depurar. Por eso se verifica no solo que fallen, sino que la
excepción sea accionable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nexo_contracts.examples import INVALID_EXAMPLES, VALID_EXAMPLES
from nexo_contracts.export import repository_root
from nexo_contracts.registry import contract_for

pytestmark = pytest.mark.contract

EXAMPLES_DIR = repository_root() / "contracts" / "examples"


@pytest.mark.parametrize("example", INVALID_EXAMPLES, ids=lambda item: item.name)
def test_invalid_example_is_rejected(example) -> None:
    with pytest.raises(ValidationError):
        contract_for(example.contract).model_validate(example.payload)


@pytest.mark.parametrize("example", INVALID_EXAMPLES, ids=lambda item: item.name)
def test_rejection_is_actionable(example) -> None:
    """El error debe señalar qué falló, no solo que algo falló."""
    with pytest.raises(ValidationError) as caught:
        contract_for(example.contract).model_validate(example.payload)
    errors = caught.value.errors()
    assert errors, "la validación falló sin detallar ningún error"
    first = errors[0]
    assert first["msg"].strip(), "el error no trae mensaje"
    assert "type" in first


def test_every_invalid_example_names_a_distinct_case() -> None:
    names = [example.name for example in INVALID_EXAMPLES]
    assert len(names) == len(set(names))


def test_published_examples_match_the_models() -> None:
    """Los archivos en disco deben coincidir con los ejemplos en código."""
    for name, model in VALID_EXAMPLES.items():
        path = EXAMPLES_DIR / "valid" / f"{name}.json"
        assert path.exists(), f"falta el ejemplo publicado {path}"
        published = json.loads(path.read_text(encoding="utf-8"))
        assert published == model.model_dump(mode="json", by_alias=True)


def test_published_invalid_examples_exist() -> None:
    for example in INVALID_EXAMPLES:
        path = EXAMPLES_DIR / "invalid" / f"{example.name}.json"
        assert path.exists(), f"falta el ejemplo inválido publicado {path}"


def test_manifest_documents_the_rejecting_rule() -> None:
    """El manifiesto es lo que consume otro equipo: debe decir por qué falla cada caso."""
    manifest = json.loads((EXAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))
    for example in INVALID_EXAMPLES:
        entry = manifest["invalid"][example.name]
        assert entry["contract"] == example.contract
        assert entry["rejected_by"].strip()


def test_domain_fixtures_are_published() -> None:
    """Los dos recorridos MVP tienen fixtures consumibles (`DIE-F0-029`)."""
    root = repository_root()
    vehiculos = sorted((root / "domains" / "vehiculos" / "fixtures").glob("*.json"))
    empresas = sorted(
        (root / "domains" / "ayuntamiento_empresas" / "fixtures").glob("*.json")
    )
    assert vehiculos, "faltan fixtures de vehículos"
    assert empresas, "faltan fixtures de apertura de empresas"


@pytest.mark.security
def test_fixtures_contain_no_obvious_pii_or_secrets() -> None:
    """Ningún fixture publicado transporta credenciales ni PII directa.

    Se excluyen `examples/invalid/`: esos payloads contienen justamente el
    contenido prohibido, porque su propósito es demostrar que se rechaza.
    """
    forbidden = ("api_key", "password", "secret:", "Bearer ", "curp", "telefono")
    root = repository_root()
    targets: list[Path] = [
        *(root / "contracts" / "examples" / "valid").rglob("*.json"),
        *(root / "domains").rglob("fixtures/*.json"),
    ]
    assert targets
    offenders: list[str] = []
    for path in targets:
        content = path.read_text(encoding="utf-8").lower()
        for needle in forbidden:
            # `secret://` es una referencia, no un secreto: es exactamente el
            # patrón que la política exige.
            if needle == "secret:" and "secret://" in content:
                continue
            if needle.lower() in content:
                offenders.append(f"{path.name}: {needle}")
    assert not offenders, f"fixtures con contenido prohibido: {offenders}"
