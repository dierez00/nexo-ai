"""Estimador determinista: DAG, orden topológico y suma en código (F1.7)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from nexo_agents.estimator import (
    Estimator,
    PermitGraph,
    PermitStep,
    VehicleEstimator,
    invalidated_by,
    load_permit_graph,
)
from nexo_contracts import (
    Domain,
    FactCategory,
    FactValue,
    Money,
    SourceCitation,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)

CITATION = SourceCitation(
    source_id="src_ayto_tarifas",
    fragment_id="frag_costos",
    corpus_version="ayuntamiento_empresas-2026-07-30",
    source_version="v2",
    valid_from=date(2026, 1, 1),
    is_active=True,
)


def _fact(fact_id: str, claim: str, category: FactCategory, **value: object) -> VerifiedFact:
    return VerifiedFact(
        fact_id=fact_id,
        claim=claim,
        value=FactValue(**value),  # type: ignore[arg-type]
        category=category,
        domain=Domain.AYUNTAMIENTO_EMPRESAS,
        verification=VerificationStatus.ACCEPTED,
        reason="citation_supports_claim",
        confidence=0.95,
        citations=[CITATION],
    )


def _facts(*facts: VerifiedFact) -> VerifiedFacts:
    return VerifiedFacts(snapshot_id="snapshot_emp", created_at=NOW, facts=facts)


@pytest.fixture(scope="module")
def graph(root: Path) -> PermitGraph:
    return load_permit_graph(root, Domain.AYUNTAMIENTO_EMPRESAS)


@pytest.fixture
def estimator(graph: PermitGraph) -> Estimator:
    return Estimator(graph=graph)


@pytest.fixture
def full_route() -> VerifiedFacts:
    """Hechos que respaldan los cuatro trámites de la ruta."""
    return _facts(
        _fact(
            "fact_uso_suelo",
            "La constancia de uso de suelo cuesta 1180.00 MXN.",
            FactCategory.COST,
            money=Money(amount_minor=118000, currency="MXN"),
        ),
        _fact(
            "fact_pc",
            "El visto bueno de protección civil cuesta 940.00 MXN.",
            FactCategory.COST,
            money=Money(amount_minor=94000, currency="MXN"),
        ),
        _fact(
            "fact_sanidad",
            "El aviso de funcionamiento sanitario no genera derechos.",
            FactCategory.COST,
            money=Money(amount_minor=0, currency="MXN"),
        ),
        _fact(
            "fact_licencia",
            "La licencia de funcionamiento municipal cuesta 2350.00 MXN.",
            FactCategory.COST,
            money=Money(amount_minor=235000, currency="MXN"),
        ),
    )


# --- El grafo se valida al cargarlo (`DIE-F1-059`) --------------------------


def test_the_repository_graph_loads_and_is_acyclic(graph: PermitGraph) -> None:
    assert [step.step_id for step in graph.steps] == [
        "uso_de_suelo",
        "proteccion_civil",
        "aviso_sanitario",
        "licencia_funcionamiento",
    ]


def test_a_cyclic_graph_is_rejected_at_load_time() -> None:
    """Es preferible no dar ruta a darla en un orden imposible."""
    with pytest.raises(ValueError, match="ciclo de dependencias"):
        PermitGraph(
            version="permits-test",
            domain=Domain.AYUNTAMIENTO_EMPRESAS,
            title="Ciclo",
            steps=[
                PermitStep(
                    step_id="paso_a", title="A", depends_on=["paso_b"], evidence_keywords=["a"]
                ),
                PermitStep(
                    step_id="paso_b", title="B", depends_on=["paso_a"], evidence_keywords=["b"]
                ),
            ],
        )


def test_a_dangling_dependency_is_rejected_at_load_time() -> None:
    with pytest.raises(ValueError, match="depende de trámites inexistentes"):
        PermitGraph(
            version="permits-test",
            domain=Domain.AYUNTAMIENTO_EMPRESAS,
            title="Colgante",
            steps=[
                PermitStep(
                    step_id="paso_a", title="A", depends_on=["fantasma"], evidence_keywords=["a"]
                )
            ],
        )


# --- Orden y suma (`DIE-F1-057`, `DIE-F1-060`) ------------------------------


def test_steps_come_in_topological_order(estimator: Estimator, full_route) -> None:
    estimate = estimator.estimate(full_route).estimate

    order = [step.step_id for step in estimate.steps]
    assert order.index("uso_de_suelo") < order.index("proteccion_civil")
    assert order.index("proteccion_civil") < order.index("licencia_funcionamiento")
    assert order.index("aviso_sanitario") < order.index("licencia_funcionamiento")


def test_the_order_is_stable_across_runs(estimator: Estimator, full_route) -> None:
    """Sin desempate determinista, ningún golden test sería comparable."""
    first = [step.step_id for step in estimator.estimate(full_route).estimate.steps]
    second = [step.step_id for step in estimator.estimate(full_route).estimate.steps]

    assert first == second


def test_the_total_is_summed_in_code_over_minor_units(estimator: Estimator, full_route) -> None:
    estimate = estimator.estimate(full_route).estimate

    # 118000 + 94000 + 0 + 235000
    assert estimate.total_cost == Money(amount_minor=447000, currency="MXN")


def test_mixed_currencies_drop_the_amount_and_keep_the_route(
    estimator: Estimator,
) -> None:
    """Una conversión implícita a mitad de un trámite no la puede auditar nadie.

    El contrato de `Estimate` prohíbe mezclar monedas, así que el estimador
    conserva la ruta —que sigue siendo correcta— y descarta el importe
    divergente con su aviso.
    """
    facts = _facts(
        _fact(
            "fact_a",
            "La constancia de uso de suelo cuesta 1180.00 MXN.",
            FactCategory.COST,
            money=Money(amount_minor=118000, currency="MXN"),
        ),
        _fact(
            "fact_b",
            "La licencia de funcionamiento cuesta 120.00 USD.",
            FactCategory.COST,
            money=Money(amount_minor=12000, currency="USD"),
        ),
    )

    outcome = estimator.estimate(facts)

    assert [step.step_id for step in outcome.estimate.steps] == [
        "uso_de_suelo",
        "licencia_funcionamiento",
    ]
    assert outcome.estimate.total_cost == Money(amount_minor=118000, currency="MXN")
    assert any("otra moneda" in warning for warning in outcome.warnings)


# --- Solo lo respaldado entra (`DIE-F1-061`, `DIE-F1-062`) ------------------


def test_a_step_without_verified_evidence_is_omitted(estimator: Estimator) -> None:
    facts = _facts(
        _fact(
            "fact_uso_suelo",
            "La constancia de uso de suelo cuesta 1180.00 MXN.",
            FactCategory.COST,
            money=Money(amount_minor=118000, currency="MXN"),
        )
    )

    outcome = estimator.estimate(facts)

    assert [step.step_id for step in outcome.estimate.steps] == ["uso_de_suelo"]
    assert set(outcome.unsupported_steps) == {
        "proteccion_civil",
        "aviso_sanitario",
        "licencia_funcionamiento",
    }
    assert outcome.warnings


def test_a_rejected_fact_never_backs_a_step(estimator: Estimator) -> None:
    """Solo los hechos aceptados sostienen la ruta."""
    rejected = VerifiedFact(
        fact_id="fact_rechazado",
        claim="La constancia de uso de suelo es gratuita.",
        value=FactValue(text="gratis"),
        category=FactCategory.COST,
        domain=Domain.AYUNTAMIENTO_EMPRESAS,
        verification=VerificationStatus.REJECTED,
        reason="source_expired",
        confidence=0.3,
    )

    outcome = estimator.estimate(_facts(rejected))

    assert outcome.estimate.steps == []


def test_every_step_records_which_facts_it_came_from(estimator: Estimator, full_route) -> None:
    """`DIE-F1-062`: sin `derived_from` no se puede invalidar un cálculo."""
    estimate = estimator.estimate(full_route).estimate

    for step in estimate.steps:
        assert step.derived_from


def test_dependencies_are_trimmed_to_the_included_steps(estimator: Estimator) -> None:
    """Apuntar a un trámite omitido dejaría una referencia irresoluble."""
    facts = _facts(
        _fact(
            "fact_licencia",
            "La licencia de funcionamiento municipal cuesta 2350.00 MXN.",
            FactCategory.COST,
            money=Money(amount_minor=235000, currency="MXN"),
        )
    )

    estimate = estimator.estimate(facts).estimate

    assert [step.step_id for step in estimate.steps] == ["licencia_funcionamiento"]
    assert estimate.steps[0].depends_on == []


def test_rejecting_a_fact_afterwards_invalidates_its_step(estimator: Estimator, full_route) -> None:
    estimate = estimator.estimate(full_route).estimate

    invalid = invalidated_by(estimate, ["fact_licencia"])

    assert invalid == ("licencia_funcionamiento",)


# --- El modelo no toca los números (`DIE-F1-063`) ---------------------------


def test_the_estimator_has_no_model_gateway(estimator: Estimator) -> None:
    """No es una regla de conducta: no hay dónde inyectarle un modelo."""
    assert "gateway" not in vars(estimator)
    assert "model" not in vars(estimator)


def test_vehicle_estimator_keeps_renewal_cost_separate_from_debt() -> None:
    renewal = VerifiedFact(
        fact_id="fact_renewal",
        claim="Renovar la licencia tipo A cuesta 814.00 MXN.",
        value=FactValue(money=Money(amount_minor=81400, currency="MXN")),
        category=FactCategory.COST,
        domain=Domain.VEHICULOS,
        verification=VerificationStatus.ACCEPTED,
        reason="citation_supports_claim",
        confidence=0.95,
        citations=[
            CITATION.model_copy(
                update={
                    "source_id": "src_veh_tarifas",
                    "fragment_id": "frag_veh_cost",
                }
            )
        ],
    )
    debt = renewal.model_copy(
        update={
            "fact_id": "fact_debt",
            "claim": "El adeudo vehicular es de 480.00 MXN.",
            "value": FactValue(money=Money(amount_minor=48000, currency="MXN")),
            "supporting_tool_call_id": "tc_000001",
            "citations": [],
        }
    )
    requirements = renewal.model_copy(
        update={
            "fact_id": "fact_docs",
            "claim": "Se requiere identificación oficial vigente.",
            "value": FactValue(items=["Identificación oficial vigente"]),
            "category": FactCategory.REQUIREMENT,
        }
    )
    facts = VerifiedFacts(
        snapshot_id="fact_vehicle",
        created_at=NOW,
        facts=(renewal, debt, requirements),
    )

    estimate = VehicleEstimator().estimate(facts).estimate

    assert estimate.total_cost == Money(amount_minor=81400, currency="MXN")
    assert estimate.steps[0].missing_documents == ["Identificación oficial vigente"]


def test_vehicle_estimator_calculates_first_time_license() -> None:
    cost = VerifiedFact(
        fact_id="fact_first_license_cost",
        claim="La primera emisión de licencia tipo A cuesta 980.00 MXN.",
        value=FactValue(money=Money(amount_minor=98000, currency="MXN")),
        category=FactCategory.COST,
        domain=Domain.VEHICULOS,
        verification=VerificationStatus.ACCEPTED,
        reason="citation_supports_claim",
        confidence=0.95,
        citations=[
            CITATION.model_copy(
                update={
                    "source_id": "src_veh_tarifas",
                    "fragment_id": "frag_veh_first_license_cost",
                }
            )
        ],
    )
    requirements = cost.model_copy(
        update={
            "fact_id": "fact_first_license_docs",
            "claim": "Para primera emisión se requiere identificación oficial, CURP y examen de manejo.",
            "value": FactValue(
                items=[
                    "CURP",
                    "Constancia de aprobación del examen de manejo",
                    "Identificación oficial vigente con fotografía",
                ]
            ),
            "category": FactCategory.REQUIREMENT,
        }
    )
    facts = VerifiedFacts(
        snapshot_id="fact_vehicle_first",
        created_at=NOW,
        facts=(cost, requirements),
    )

    estimate = VehicleEstimator().estimate(facts).estimate

    assert estimate.steps[0].step_id == "primera_emision_licencia"
    assert estimate.steps[0].title == "Tramitar licencia de conducir por primera vez"
    assert estimate.total_cost == Money(amount_minor=98000, currency="MXN")
    assert "CURP" in estimate.steps[0].missing_documents
