"""Clasificador: catálogo cerrado, intenciones separadas y fallback (F1.4)."""

from __future__ import annotations

from typing import Any

import pytest

from nexo_agents.classifier import PURPOSE, Classifier, classify_by_keywords
from nexo_agents.domain_manifest import DomainManifest
from nexo_contracts import (
    Classification,
    DetectedIntent,
    Domain,
    ErrorCode,
    OperationalUrgency,
)
from nexo_orchestration.testing import FakeBehavior, Scenario

pytestmark = pytest.mark.unit

CAP_VEH_01 = "Quiero renovar mi licencia y saber si debo algo"
CAP_EMP_01 = "Quiero abrir una taquería en Durango"


def _payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "intents": [
            {"intent": "renovar_licencia", "domain": "vehiculos", "confidence": 0.94},
            {"intent": "consultar_adeudo", "domain": "vehiculos", "confidence": 0.88},
        ],
        "location": "Durango",
        "audience": "citizen",
        "urgency": "routine",
        "entities": {"tipo_licencia": "A"},
        "missing_information": [],
        "confidence": 0.91,
    }
    payload.update(overrides)
    return payload


def _classifier(
    manifests: dict[Domain, DomainManifest], gateway_factory: Any, scenarios: Any
) -> Classifier:
    return Classifier(gateway=gateway_factory({PURPOSE: scenarios}), manifests=manifests)


# --- DIE-F1-032: las dos intenciones no se fusionan --------------------------


async def test_the_two_official_intents_stay_separate(
    manifests, gateway_factory, request_factory, context
) -> None:
    """`CAP-VEH-01` existe para detectar exactamente este error."""
    classifier = _classifier(manifests, gateway_factory, Scenario(data=_payload()))

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.classification.intent_slugs() == ("renovar_licencia", "consultar_adeudo")
    assert result.used_fallback is False


def test_the_deterministic_fallback_also_separates_them(manifests) -> None:
    """Sin modelo, los casos oficiales deben seguir clasificando (`DIE-F1-034`)."""
    classification = classify_by_keywords(CAP_VEH_01, manifests)

    assert set(classification.intent_slugs()) >= {"renovar_licencia", "consultar_adeudo"}


def test_the_fallback_resolves_the_business_case(manifests) -> None:
    classification = classify_by_keywords(CAP_EMP_01, manifests)

    assert "abrir_negocio" in classification.intent_slugs()
    assert classification.primary_domain is Domain.AYUNTAMIENTO_EMPRESAS


def test_the_fallback_declares_out_of_scope_instead_of_guessing(manifests) -> None:
    """`DIE-F1-035`: no inventar dominio es preferible a acertar por azar."""
    classification = classify_by_keywords("cómo tramito mi pasaporte", manifests)

    assert classification.is_out_of_scope is True
    assert classification.intents == []


def test_keyword_matching_respects_word_boundaries(manifests) -> None:
    """«debo» no debe dispararse dentro de otra palabra."""
    assert classify_by_keywords("adebolizar el proceso", manifests).is_out_of_scope is True


# --- DIE-F1-034: el fallback cubre cada modo de fallo del modelo -------------


@pytest.mark.parametrize(
    "behavior",
    [FakeBehavior.PROVIDER_DOWN, FakeBehavior.RATE_LIMIT, FakeBehavior.TIMEOUT],
)
async def test_a_failing_provider_falls_back_to_keywords(
    manifests, gateway_factory, request_factory, context, behavior
) -> None:
    classifier = _classifier(manifests, gateway_factory, Scenario(behavior=behavior))

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.used_fallback is True
    assert set(result.classification.intent_slugs()) >= {"renovar_licencia", "consultar_adeudo"}
    assert "deterministic_fallback" in result.self_check.notes


async def test_output_that_breaks_the_schema_falls_back(
    manifests, gateway_factory, request_factory, context
) -> None:
    classifier = _classifier(
        manifests, gateway_factory, Scenario(data={"intents": "no es una lista"})
    )

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.used_fallback is True
    assert result.error is not None


async def test_an_invented_intent_falls_back_instead_of_propagating(
    manifests, gateway_factory, request_factory, context
) -> None:
    """El schema no puede atrapar esto: los slugs válidos viven en configuración.

    El modelo cumple el contrato y aun así propone un trámite que nadie sabe
    atender. Sin esta comprobación, el supervisor delegaría a un navegador que
    no tiene ni fuentes ni tools para esa intención.
    """
    classifier = _classifier(
        manifests,
        gateway_factory,
        Scenario(
            data=_payload(
                intents=[{"intent": "tramitar_visa", "domain": "vehiculos", "confidence": 0.9}]
            )
        ),
    )

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.used_fallback is True
    assert result.error is not None
    assert result.error.code is ErrorCode.MODEL_OUTPUT_INVALID
    assert "tramitar_visa" in result.error.message


async def test_an_intent_assigned_to_the_wrong_domain_is_rejected(
    manifests, gateway_factory, request_factory, context
) -> None:
    """`renovar_licencia` existe, pero no en `ayuntamiento_empresas`."""
    classifier = _classifier(
        manifests,
        gateway_factory,
        Scenario(
            data=_payload(
                intents=[
                    {
                        "intent": "renovar_licencia",
                        "domain": "ayuntamiento_empresas",
                        "confidence": 0.9,
                    }
                ]
            )
        ),
    )

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.used_fallback is True


# --- DIE-F1-033: el clasificador no puede hacer nada más --------------------


def test_the_classifier_has_no_retriever_and_no_tool_executor(manifests, gateway_factory) -> None:
    """No es una regla de conducta: no recibe los puertos en su constructor."""
    classifier = _classifier(manifests, gateway_factory, Scenario(data=_payload()))

    attributes = set(vars(classifier))
    assert "retriever" not in attributes
    assert "tool_executor" not in attributes
    assert "executor" not in attributes


def test_the_classification_contract_cannot_carry_an_action() -> None:
    """`Classification` no tiene dónde poner una tool ni una respuesta."""
    fields = set(Classification.model_fields)

    assert not fields & {"tools", "proposed_tools", "answer", "citations", "actions"}


async def test_the_self_check_reports_no_forbidden_tool_requests(
    manifests, gateway_factory, request_factory, context
) -> None:
    classifier = _classifier(manifests, gateway_factory, Scenario(data=_payload()))

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.self_check.forbidden_tool_requests == 0
    assert result.self_check.passed is True


# --- DIE-F1-035: ambigüedad declarada ---------------------------------------


async def test_declared_ambiguity_survives_to_the_result(
    manifests, gateway_factory, request_factory, context
) -> None:
    classifier = _classifier(
        manifests,
        gateway_factory,
        Scenario(
            data=_payload(
                is_ambiguous=True,
                ambiguity_reason="No queda claro si quiere renovar o sacar la primera licencia.",
            )
        ),
    )

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    assert result.classification.is_ambiguous is True
    assert "ambiguity_declared" in result.self_check.notes


def test_an_ambiguous_classification_must_explain_itself() -> None:
    with pytest.raises(ValueError, match="debe decir por qué"):
        Classification(entities={}, is_ambiguous=True)


def test_a_classification_that_commits_to_nothing_is_rejected() -> None:
    """Cero intenciones sin motivo dejaría el run sin dominio y sin explicación."""
    with pytest.raises(ValueError, match="necesita un motivo"):
        Classification(entities={})


def test_out_of_scope_and_intents_cannot_both_be_true() -> None:
    with pytest.raises(ValueError, match="no pueden ser ciertas a la vez"):
        Classification(
            entities={},
            is_out_of_scope=True,
            intents=[
                DetectedIntent(intent="renovar_licencia", domain=Domain.VEHICULOS, confidence=0.9)
            ],
        )


# --- DIE-F1-031: extracción de contexto -------------------------------------


async def test_location_profile_entities_and_gaps_are_preserved(
    manifests, gateway_factory, request_factory, context
) -> None:
    classifier = _classifier(
        manifests,
        gateway_factory,
        Scenario(data=_payload(missing_information=["numero_de_licencia"], urgency="urgent")),
    )

    result = await classifier.classify(request_factory(CAP_VEH_01), context)

    classification = result.classification
    assert classification.location == "Durango"
    assert classification.entities == {"tipo_licencia": "A"}
    assert classification.missing_information == ["numero_de_licencia"]
    assert classification.urgency is OperationalUrgency.URGENT


# --- Catálogo cerrado -------------------------------------------------------


def test_the_prompt_only_offers_declared_intents(manifests, gateway_factory) -> None:
    classifier = _classifier(manifests, gateway_factory, Scenario(data=_payload()))

    catalog = classifier.catalog_text()

    for slug in classifier.known_slugs():
        assert f"`{slug}`" in catalog
    assert "tramitar_visa" not in catalog
