"""Navegador de dominio: grounding, allowlists y self-check (F1.5).

La prueba central de este archivo es que **el modelo no puede inventar una
fuente**, porque no escribe las citaciones: solo referencia identificadores de
fragmentos que se le mostraron, y el navegador resuelve el resto.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from nexo_agents.classifier import classify_by_keywords
from nexo_agents.domain_manifest import DomainManifest
from nexo_agents.navigator import PURPOSE, DomainNavigator
from nexo_contracts import (
    Domain,
    FactCategory,
    FactOrigin,
    RetrievalFilters,
    RetrievalQuery,
    SourceStatus,
    TaskStatus,
    ToolMode,
)
from nexo_orchestration.testing import FakeBehavior, Scenario

pytestmark = pytest.mark.unit

VALID_AT = date(2026, 7, 30)
CAP_VEH_01 = "Quiero renovar mi licencia y saber si debo algo"


@pytest.fixture
async def real_fragment(corpus) -> str:
    """Un `fragment_id` que el retriever devuelve de verdad para el caso oficial."""
    response = await corpus.retriever(Domain.VEHICULOS).retrieve(
        RetrievalQuery(
            query="requisitos para renovar la licencia de conducir",
            domain=Domain.VEHICULOS,
            filters=RetrievalFilters(
                institution_id="inst_demo", status=[SourceStatus.ACTIVE], valid_at=VALID_AT
            ),
            top_k=5,
        )
    )
    return response.results[0].fragment_id


def _navigator(manifests, corpus, gateway_factory, data: dict[str, Any]) -> DomainNavigator:
    return DomainNavigator(
        domain=Domain.VEHICULOS,
        manifest=manifests[Domain.VEHICULOS],
        gateway=gateway_factory({PURPOSE: Scenario(data=data)}),
        retriever=corpus.retriever(Domain.VEHICULOS),
    )


async def _navigate(navigator, request_factory, context, message: str = CAP_VEH_01):
    request = request_factory(message)
    classification = classify_by_keywords(message, {Domain.VEHICULOS: navigator.manifest})
    return await navigator.navigate(request, classification, context, valid_at=VALID_AT)


def _fact(fragment: str, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "claim": "Se requiere identificación oficial vigente.",
        "category": "requirement",
        "value": {"items": ["Identificación oficial vigente"]},
        "fragment_ids": [fragment],
        "confidence": 0.9,
    }
    payload.update(overrides)
    return payload


# --- Grounding (`DIE-F1-041`, `DIE-F1-045`) ---------------------------------


async def test_a_fact_citing_real_evidence_keeps_its_citation(
    manifests, corpus, gateway_factory, request_factory, context, real_fragment
) -> None:
    navigator = _navigator(manifests, corpus, gateway_factory, {"facts": [_fact(real_fragment)]})

    result = await _navigate(navigator, request_factory, context)

    assert len(result.facts) == 1
    fact = result.facts[0]
    assert fact.origin is FactOrigin.RAG
    assert fact.citations[0].fragment_id == real_fragment
    assert fact.citations[0].is_active is True
    assert result.self_check.unsupported_claims == 0


@pytest.mark.security
async def test_a_critical_fact_citing_an_invented_fragment_is_discarded(
    manifests, corpus, gateway_factory, request_factory, context, real_fragment
) -> None:
    """El modelo no puede inventar una fuente porque no escribe la citación."""
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {
            "facts": [
                _fact(real_fragment),
                _fact(
                    "frag_inventadoxxxxx",
                    claim="La renovación cuesta 500 MXN.",
                    category="cost",
                    value={"money": {"amount_minor": 50000, "currency": "MXN"}},
                ),
            ]
        },
    )

    result = await _navigate(navigator, request_factory, context)

    claims = [fact.claim for fact in result.facts]
    assert "La renovación cuesta 500 MXN." not in claims
    assert result.self_check.unsupported_claims == 1
    assert result.self_check.passed is False


@pytest.mark.security
async def test_a_critical_fact_without_any_citation_is_discarded(
    manifests, corpus, gateway_factory, request_factory, context
) -> None:
    """Un costo sin fuente no se degrada: se descarta (gate de grounding)."""
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {
            "facts": [
                _fact(
                    "",
                    fragment_ids=[],
                    claim="La renovación cuesta 814 MXN.",
                    category="cost",
                    value={"money": {"amount_minor": 81400, "currency": "MXN"}},
                )
            ]
        },
    )

    result = await _navigate(navigator, request_factory, context)

    assert result.facts == ()
    assert result.self_check.unsupported_claims == 1


async def test_a_non_critical_fact_without_citation_survives_as_orientation(
    manifests, corpus, gateway_factory, request_factory, context
) -> None:
    """Orientar sin citar es legítimo; afirmar un requisito o un costo no lo es."""
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {
            "facts": [
                _fact(
                    "",
                    fragment_ids=[],
                    claim="El trámite es presencial.",
                    category="procedure",
                    value={"text": "presencial"},
                )
            ]
        },
    )

    result = await _navigate(navigator, request_factory, context)

    assert len(result.facts) == 1
    assert result.facts[0].origin is FactOrigin.DEDUCTION
    assert result.facts[0].deduction is not None
    assert result.facts[0].deduction.confirmed_by_user is False
    assert result.facts[0].deduction.write_eligible is False
    assert result.self_check.unsupported_claims == 0


@pytest.mark.parametrize(
    "category",
    [
        FactCategory.REQUIREMENT,
        FactCategory.COST,
        FactCategory.LOCATION,
        FactCategory.VALIDITY,
        FactCategory.DEPENDENCY,
    ],
)
async def test_every_critical_category_needs_evidence(
    manifests, corpus, gateway_factory, request_factory, context, category
) -> None:
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {
            "facts": [
                _fact(
                    "",
                    fragment_ids=[],
                    category=category.value,
                    value={"text": "algo"},
                )
            ]
        },
    )

    result = await _navigate(navigator, request_factory, context)

    assert result.facts == ()


# --- Allowlist de tools (`DIE-F1-040`, `DIE-F1-042`) ------------------------


@pytest.mark.security
async def test_write_tools_and_foreign_tools_are_filtered_out(
    manifests, corpus, gateway_factory, request_factory, context, real_fragment
) -> None:
    """Un navegador no propone escrituras ni tools de otro dominio."""
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {
            "facts": [_fact(real_fragment)],
            "proposed_tools": [
                {"name": "vehiculos.consultar_adeudo", "rationale": "hay que ver el saldo"},
                {"name": "vehiculos.reservar_cita", "rationale": "agendar ya"},
                {"name": "ayuntamiento.consultar_citas", "rationale": "otro dominio"},
                {"name": "vehiculos.tool_inventada", "rationale": "no existe"},
            ],
        },
    )

    result = await _navigate(navigator, request_factory, context)

    assert [tool.name for tool in result.proposed_tools] == ["vehiculos.consultar_adeudo"]
    assert result.self_check.forbidden_tool_requests == 3


async def test_proposed_tools_are_always_read_mode(
    manifests, corpus, gateway_factory, request_factory, context, real_fragment
) -> None:
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {
            "facts": [_fact(real_fragment)],
            "proposed_tools": [{"name": "vehiculos.buscar_citas", "rationale": "ver slots"}],
        },
    )

    result = await _navigate(navigator, request_factory, context)

    assert all(tool.mode is ToolMode.READ for tool in result.proposed_tools)


def test_a_navigator_cannot_be_built_with_another_domains_manifest(
    manifests, corpus, gateway_factory
) -> None:
    with pytest.raises(ValueError, match="recibió el manifiesto"):
        DomainNavigator(
            domain=Domain.VEHICULOS,
            manifest=manifests[Domain.AYUNTAMIENTO_EMPRESAS],
            gateway=gateway_factory({}),
            retriever=corpus.retriever(Domain.VEHICULOS),
        )


def test_the_manifest_rejects_tools_from_another_domain(manifests) -> None:
    """El límite del namespace se valida al cargar el manifiesto, no en ejecución."""
    payload = manifests[Domain.VEHICULOS].model_dump(mode="json")
    payload["allowed_tools"] = ["ayuntamiento.consultar_citas"]

    with pytest.raises(ValueError, match="declara tools ajenas"):
        DomainManifest.model_validate(payload)


# --- Prompt injection (`DIE-F1-025`, `DIE-F1-026`) --------------------------


@pytest.mark.security
async def test_flagged_evidence_is_never_used_as_support(
    manifests, corpus, gateway_factory, request_factory, context
) -> None:
    """El documento manipulado se recupera, se advierte y no respalda nada."""
    navigator = _navigator(manifests, corpus, gateway_factory, {"facts": []})

    result = await _navigate(
        navigator, request_factory, context, "nota administrativa sobre horarios de módulos"
    )

    assert any("anómalo" in warning for warning in result.warnings)


# --- Preguntas mínimas (`DIE-F1-044`) ---------------------------------------


async def test_a_question_is_forwarded_when_the_domain_allows_one(
    manifests, corpus, gateway_factory, request_factory, context, real_fragment
) -> None:
    navigator = _navigator(
        manifests,
        corpus,
        gateway_factory,
        {"facts": [_fact(real_fragment)], "question": "¿Tu licencia es tipo A?"},
    )

    result = await _navigate(navigator, request_factory, context)

    assert result.question == "¿Tu licencia es tipo A?"


async def test_no_question_is_asked_when_the_budget_is_zero(
    manifests, corpus, gateway_factory, request_factory, context, real_fragment
) -> None:
    """Preguntar «por si acaso» convierte un trámite en una conversación."""
    manifest = manifests[Domain.VEHICULOS]
    silent = manifest.model_copy(
        update={"policies": manifest.policies.model_copy(update={"max_questions": 0})}
    )
    navigator = DomainNavigator(
        domain=Domain.VEHICULOS,
        manifest=silent,
        gateway=gateway_factory(
            {PURPOSE: Scenario(data={"facts": [_fact(real_fragment)], "question": "¿Tipo A?"})}
        ),
        retriever=corpus.retriever(Domain.VEHICULOS),
    )

    result = await _navigate(navigator, request_factory, context)

    assert result.question is None


# --- Fallos del modelo -------------------------------------------------------


async def test_a_failing_model_produces_a_failed_result_not_an_invented_one(
    manifests, corpus, gateway_factory, request_factory, context
) -> None:
    navigator = DomainNavigator(
        domain=Domain.VEHICULOS,
        manifest=manifests[Domain.VEHICULOS],
        gateway=gateway_factory({PURPOSE: Scenario(behavior=FakeBehavior.PROVIDER_DOWN)}),
        retriever=corpus.retriever(Domain.VEHICULOS),
    )

    result = await _navigate(navigator, request_factory, context)

    assert result.status is TaskStatus.FAILED
    assert result.facts == ()
    assert result.error is not None


async def test_no_evidence_produces_partial_without_facts(
    manifests, corpus, gateway_factory, request_factory, context
) -> None:
    navigator = _navigator(manifests, corpus, gateway_factory, {"facts": []})

    result = await _navigate(navigator, request_factory, context, "cómo saco mi pasaporte")

    assert result.facts == ()
    assert result.status is TaskStatus.PARTIAL
