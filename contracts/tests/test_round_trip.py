"""Round-trip JSON de cada contrato publicado (§7.8).

Un contrato que no sobrevive su propia serialización no es transportable: el
backend no puede enviarlo, el checkpoint no puede guardarlo y el frontend no
puede leerlo. Esta prueba recorre el registro completo, así que un contrato
nuevo queda cubierto por el solo hecho de publicarse.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from nexo_contracts.examples import VALID_EXAMPLES
from nexo_contracts.registry import CONTRACT_REGISTRY, contract_for

pytestmark = pytest.mark.contract


@pytest.mark.parametrize("name", sorted(CONTRACT_REGISTRY))
def test_every_contract_has_a_canonical_example(name: str) -> None:
    assert name in VALID_EXAMPLES, (
        f"el contrato {name!r} está publicado pero no tiene ejemplo canónico; "
        f"añádelo en nexo_contracts.examples"
    )


@pytest.mark.parametrize("name", sorted(VALID_EXAMPLES))
def test_round_trip_preserves_the_model(name: str) -> None:
    original = VALID_EXAMPLES[name]
    assert original.round_trip() == original


@pytest.mark.parametrize("name", sorted(VALID_EXAMPLES))
def test_serialization_is_valid_json(name: str) -> None:
    payload = VALID_EXAMPLES[name].model_dump_json(by_alias=True)
    assert isinstance(json.loads(payload), dict)


@pytest.mark.parametrize("name", sorted(VALID_EXAMPLES))
def test_round_trip_is_stable_across_repetitions(name: str) -> None:
    """Serializar dos veces produce los mismos bytes: sin sets ni orden aleatorio."""
    model = VALID_EXAMPLES[name]
    assert model.model_dump_json(by_alias=True) == model.model_dump_json(by_alias=True)


@pytest.mark.parametrize("name", sorted(VALID_EXAMPLES))
def test_wire_dump_drops_internal_fields(name: str) -> None:
    model = VALID_EXAMPLES[name]
    internal = type(model).internal_field_names()
    if not internal:
        pytest.skip("el contrato no declara campos internos")
    wire = model.model_dump_wire()
    assert not (internal & wire.keys()), (
        f"{name} filtró campos internos al wire format: {sorted(internal & wire.keys())}"
    )


# `a2ui_component` es la única excepción y es deliberada: absorbe las propiedades
# aplanadas del protocolo A2UI dentro de `properties`. Ver la prueba dedicada
# más abajo.
_ABSORBS_UNKNOWN_PROPERTIES = {"a2ui_component"}


@pytest.mark.parametrize(
    "name", sorted(set(VALID_EXAMPLES) - _ABSORBS_UNKNOWN_PROPERTIES)
)
def test_contracts_reject_unknown_properties(name: str) -> None:
    """`extra=forbid` es transversal: un campo desconocido es un error de contrato."""
    payload = VALID_EXAMPLES[name].model_dump(mode="json", by_alias=True)
    payload["__campo_no_declarado__"] = "x"
    with pytest.raises(ValidationError):
        contract_for(name).model_validate(payload)


def test_a2ui_component_absorbs_unknown_properties_by_design() -> None:
    """Documenta un límite conocido del contrato de componentes A2UI.

    El protocolo aplana las propiedades específicas de cada componente junto a
    `id` y `component`, así que el contrato no puede distinguir una propiedad
    legítima de una mal escrita: qué propiedades admite `Checklist` lo sabe el
    catálogo, no el modelo. Por eso `A2UIComponent` las absorbe en `properties`
    y quien cierra la allowlist es el validador de catálogo (`DIE-F1-104`, Fase 1).

    Lo que sí impide el contrato hoy es que esas propiedades transporten
    secretos, PII o estructuras no serializables.
    """
    from nexo_contracts import A2UIComponent

    absorbed = A2UIComponent.model_validate(
        {"id": "title", "component": "Text", "propiedad_inventada": "x"}
    )
    assert absorbed.properties == {"propiedad_inventada": "x"}

    with pytest.raises(ValidationError):
        A2UIComponent.model_validate(
            {"id": "title", "component": "Text", "api_key": "sk-demo"}
        )
