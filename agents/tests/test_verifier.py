"""Verificador secuencial: rechazo con motivo estable y bloqueo de escrituras (F1.6)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from nexo_agents.verifier import Verifier
from nexo_contracts import (
    CandidateFact,
    ContradictionSeverity,
    FactCategory,
    FactOrigin,
    FactValue,
    Money,
    RetrievalResult,
    SourceCitation,
    ToolCallStatus,
    ToolConfirmation,
    ToolResult,
    VerificationStatus,
)

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)
TODAY = date(2026, 7, 30)
FRAGMENT = "frag_requisitos"
EVIDENCE_TEXT = (
    "Para renovar una licencia tipo A se requiere presentar identificación oficial "
    "vigente, comprobante de domicilio y la licencia anterior. El costo de la "
    "renovación a tres años es de 814.00 MXN."
)


def _citation(**overrides: object) -> SourceCitation:
    payload: dict[str, object] = {
        "source_id": "src_veh_licencias",
        "fragment_id": FRAGMENT,
        "corpus_version": "vehiculos-2026-07-30",
        "source_version": "v3",
        "valid_from": date(2026, 1, 1),
        "is_active": True,
    }
    payload.update(overrides)
    return SourceCitation(**payload)  # type: ignore[arg-type]


def _evidence(text: str = EVIDENCE_TEXT, fragment: str = FRAGMENT) -> RetrievalResult:
    return RetrievalResult(
        fragment_id=fragment,
        source_id="src_veh_licencias",
        title="Requisitos",
        text=text,
        fused_score=0.8,
        citation=_citation(fragment_id=fragment),
    )


def _candidate(**overrides: object) -> CandidateFact:
    payload: dict[str, object] = {
        "fact_id": "fact_req_01",
        "claim": "Se requiere identificación oficial vigente.",
        "value": FactValue(items=["Identificación oficial vigente"]),
        "category": FactCategory.REQUIREMENT,
        "domain": "vehiculos",
        "origin": FactOrigin.RAG,
        "confidence": 0.9,
        "citations": [_citation()],
    }
    payload.update(overrides)
    return CandidateFact(**payload)  # type: ignore[arg-type]


@pytest.fixture
def verifier() -> Verifier:
    return Verifier(institution_id="inst_demo", now=NOW, valid_at=TODAY)


def _verify(verifier: Verifier, *candidates: CandidateFact, **kwargs: object):
    return verifier.verify(
        candidates, snapshot_id="snapshot_test", evidence=[_evidence()], **kwargs
    )


# --- Camino feliz -----------------------------------------------------------


def test_a_cited_requirement_is_accepted(verifier: Verifier) -> None:
    outcome = _verify(verifier, _candidate())

    fact = outcome.verified_facts.facts[0]
    assert fact.verification is VerificationStatus.ACCEPTED
    assert fact.reason == "citation_supports_claim"
    assert fact.write_eligible is True


def test_the_verifier_does_not_write_an_answer(verifier: Verifier) -> None:
    """`DIE-F1-055`: emite hechos, no prosa."""
    outcome = _verify(verifier, _candidate())

    assert not hasattr(outcome, "answer")
    assert not hasattr(outcome.verified_facts, "answer")


# --- Rechazos con motivo estable (`DIE-F1-050`, `DIE-F1-052`) ---------------


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"citations": [_citation(is_active=False)]}, "source_expired"),
        (
            {"citations": [_citation(valid_to=date(2025, 12, 31))]},
            "source_expired",
        ),
        ({"citations": [_citation(fragment_id="frag_inexistente")]}, "source_not_retrieved"),
        (
            # Origen `catalog` porque el contrato impide construir un hecho
            # `rag` sin citación: la primera barrera está antes del verificador.
            {"citations": [], "origin": FactOrigin.CATALOG},
            "critical_claim_without_evidence",
        ),
    ],
)
def test_a_critical_fact_is_rejected_with_a_stable_reason(
    verifier: Verifier, overrides: dict[str, object], expected_reason: str
) -> None:
    outcome = _verify(verifier, _candidate(**overrides))

    fact = outcome.verified_facts.facts[0]
    assert fact.verification is VerificationStatus.REJECTED
    assert fact.reason == expected_reason
    assert fact.write_eligible is False


@pytest.mark.security
def test_a_citation_from_another_source_is_rejected(verifier: Verifier) -> None:
    """El fragmento existe, pero pertenece a otra fuente que la citada."""
    outcome = _verify(verifier, _candidate(citations=[_citation(source_id="src_ayto_tarifas")]))

    assert outcome.verified_facts.facts[0].reason == "wrong_institution"


@pytest.mark.security
def test_a_citation_that_does_not_talk_about_the_claim_is_rejected(
    verifier: Verifier,
) -> None:
    """`DIE-F1-049`: existir no basta; la citación debe sostener el claim."""
    outcome = _verify(
        verifier,
        _candidate(
            claim="El trámite de ganadería exige certificado zoosanitario de movilización.",
        ),
    )

    assert outcome.verified_facts.facts[0].reason == "citation_does_not_support_claim"


def test_a_non_critical_fact_survives_without_citations(verifier: Verifier) -> None:
    """Orientar sin citar es legítimo; afirmar un requisito no lo es."""
    outcome = _verify(
        verifier,
        _candidate(
            fact_id="fact_proc_01",
            category=FactCategory.PROCEDURE,
            origin=FactOrigin.CATALOG,
            claim="El trámite es presencial.",
            value=FactValue(text="presencial"),
            citations=[],
        ),
    )

    fact = outcome.verified_facts.facts[0]
    assert fact.verification is VerificationStatus.ACCEPTED
    assert fact.write_eligible is False


# --- Hechos de tool (`DIE-F1-054`) -------------------------------------------


def _tool_result(**overrides: object) -> ToolResult:
    payload: dict[str, object] = {
        "tool_call_id": "tc_01",
        "name": "vehiculos.reservar_cita",
        "status": ToolCallStatus.SUCCEEDED,
        "duration_ms": 40,
        "confirmation": ToolConfirmation(identifier="NEXO-MOCK-01", issued_at=NOW),
    }
    payload.update(overrides)
    return ToolResult(**payload)  # type: ignore[arg-type]


def test_an_action_result_with_a_verifiable_folio_is_accepted(verifier: Verifier) -> None:
    candidate = _candidate(
        fact_id="fact_action_01",
        category=FactCategory.ACTION_RESULT,
        origin=FactOrigin.TOOL,
        tool_call_id="tc_01",
        claim="La cita quedó reservada.",
        value=FactValue(text="NEXO-MOCK-01"),
        citations=[],
    )

    outcome = verifier.verify(
        [candidate], snapshot_id="s", evidence=[_evidence()], tool_results=[_tool_result()]
    )

    assert outcome.verified_facts.facts[0].verification is VerificationStatus.ACCEPTED


@pytest.mark.security
def test_an_action_result_without_a_folio_is_rejected(verifier: Verifier) -> None:
    """Sin identificador verificable no hay éxito, aunque la tool diga que sí."""
    candidate = _candidate(
        fact_id="fact_action_01",
        category=FactCategory.ACTION_RESULT,
        origin=FactOrigin.TOOL,
        tool_call_id="tc_01",
        claim="La cita quedó reservada.",
        value=FactValue(text="ok"),
        citations=[],
    )

    outcome = verifier.verify(
        [candidate],
        snapshot_id="s",
        evidence=[_evidence()],
        tool_results=[_tool_result(confirmation=None)],
    )

    assert outcome.verified_facts.facts[0].reason == "unverifiable_action_result"


@pytest.mark.security
def test_the_contract_blocks_a_rag_fact_without_citations() -> None:
    """La primera barrera está antes del verificador, en el propio contrato."""
    with pytest.raises(ValueError, match="debe incluir al menos una citación"):
        _candidate(citations=[])


def test_a_fact_whose_tool_call_failed_is_rejected(verifier: Verifier) -> None:
    from nexo_contracts import ErrorCode, NormalizedError, ToolError

    candidate = _candidate(
        fact_id="fact_tool_01",
        origin=FactOrigin.TOOL,
        tool_call_id="tc_01",
        citations=[],
    )
    failed = _tool_result(
        status=ToolCallStatus.FAILED,
        confirmation=None,
        error=ToolError(
            error=NormalizedError.from_code(ErrorCode.TOOL_TIMEOUT, "sin respuesta"),
            safe_details={},
        ),
    )

    outcome = verifier.verify(
        [candidate], snapshot_id="s", evidence=[_evidence()], tool_results=[failed]
    )

    assert outcome.verified_facts.facts[0].reason == "tool_call_failed"


def test_a_tool_fact_without_its_result_is_rejected(verifier: Verifier) -> None:
    candidate = _candidate(origin=FactOrigin.TOOL, tool_call_id="tc_99", citations=[])

    outcome = _verify(verifier, candidate)

    assert outcome.verified_facts.facts[0].reason == "tool_result_missing"


# --- Dependencias (`DIE-F1-053`) --------------------------------------------


def test_rejecting_a_fact_invalidates_everything_that_depended_on_it(
    verifier: Verifier,
) -> None:
    """Se propaga hasta punto fijo: A→B→C, rechazar C invalida los tres."""
    base = _candidate(
        fact_id="fact_base", citations=[], origin=FactOrigin.CATALOG
    )  # crítico sin evidencia
    middle = _candidate(fact_id="fact_middle", depends_on=["fact_base"])
    top = _candidate(fact_id="fact_top", depends_on=["fact_middle"])

    outcome = _verify(verifier, base, middle, top)

    statuses = {fact.fact_id: fact.verification for fact in outcome.verified_facts.facts}
    assert all(status is VerificationStatus.REJECTED for status in statuses.values())
    reasons = {fact.fact_id: fact.reason for fact in outcome.verified_facts.facts}
    assert reasons["fact_middle"] == "depends_on_rejected_fact"
    assert reasons["fact_top"] == "depends_on_rejected_fact"


def test_the_snapshot_closes_even_when_everything_was_rejected(verifier: Verifier) -> None:
    """El contrato de `VerifiedFacts` rechazaría un snapshot incoherente."""
    outcome = _verify(verifier, _candidate(citations=[], origin=FactOrigin.CATALOG))

    assert outcome.verified_facts.accepted() == ()
    assert outcome.warnings


# --- Contradicciones (`DIE-F1-051`) -----------------------------------------


def test_a_document_and_a_tool_that_disagree_are_flagged(verifier: Verifier) -> None:
    documented = _candidate(
        fact_id="fact_cost_doc",
        category=FactCategory.COST,
        claim="El costo de renovación es de 814.00 MXN.",
        value=FactValue(money=Money(amount_minor=81400, currency="MXN")),
    )
    from_tool = _candidate(
        fact_id="fact_cost_tool",
        category=FactCategory.COST,
        origin=FactOrigin.TOOL,
        tool_call_id="tc_01",
        claim="El costo de renovación es de 900.00 MXN.",
        value=FactValue(money=Money(amount_minor=90000, currency="MXN")),
        citations=[],
    )

    outcome = verifier.verify(
        [documented, from_tool],
        snapshot_id="s",
        evidence=[_evidence()],
        tool_results=[_tool_result()],
        contradiction_id="contra_01",
    )

    assert outcome.verified_facts.contradictions
    assert outcome.verified_facts.contradictions[0].severity is ContradictionSeverity.CRITICAL
    assert outcome.verified_facts.contradictions[0].blocks_writes is True


def test_unrelated_values_in_the_same_category_are_not_a_contradiction(
    verifier: Verifier,
) -> None:
    documented = _candidate(
        fact_id="fact_license_cost",
        category=FactCategory.COST,
        claim="El costo de renovación de licencia es de 814.00 MXN.",
        value=FactValue(money=Money(amount_minor=81400, currency="MXN")),
    )
    from_tool = _candidate(
        fact_id="fact_vehicle_debt",
        category=FactCategory.COST,
        origin=FactOrigin.TOOL,
        tool_call_id="tc_01",
        claim="El adeudo vehicular consultado es de 0.00 MXN.",
        value=FactValue(money=Money(amount_minor=0, currency="MXN")),
        citations=[],
    )

    outcome = verifier.verify(
        [documented, from_tool],
        snapshot_id="s",
        evidence=[_evidence()],
        tool_results=[_tool_result()],
        contradiction_id="contra_01",
    )

    assert outcome.verified_facts.contradictions == ()
