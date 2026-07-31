"""Invariantes de estado, escrituras y evidencia (§7.8).

Estas pruebas no verifican tipos: verifican reglas de negocio codificadas en los
contratos. Son las que impiden que una escritura ocurra sin confirmación o que
un hecho crítico se afirme sin fuente.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from nexo_contracts import (
    ActionRequest,
    ActionStatus,
    AgentName,
    AgentResult,
    CandidateFact,
    Channel,
    Domain,
    ErrorCode,
    FactCategory,
    FactOrigin,
    FactValue,
    Identity,
    Money,
    NormalizedError,
    Outcome,
    ProposedToolCall,
    RunRequest,
    RunState,
    RunStatus,
    SelfCheckResult,
    TaskStatus,
    ToolCall,
    ToolMetadata,
    ToolMode,
    ToolPermissionContext,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_contracts.examples import LICENSE_CITATION

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


def _request(**overrides) -> RunRequest:
    payload = {
        "run_id": "run_000001",
        "trace_id": "trace_000001",
        "conversation_id": "conv_000001",
        "user_message": "hola",
        "channel": Channel.WEB,
        "identity": Identity(user_id="usr_demo", institution_id="inst_demo", roles=["citizen"]),
        "received_at": NOW,
    }
    payload.update(overrides)
    return RunRequest(**payload)


def _state(**overrides) -> RunState:
    request = _request()
    payload = {
        "run_id": request.run_id,
        "trace_id": request.trace_id,
        "conversation_id": request.conversation_id,
        "request": request,
        "created_at": NOW,
        "updated_at": NOW,
    }
    payload.update(overrides)
    return RunState(**payload)


# --- Estado serializable (`DIE-F0-015`) -------------------------------------


def test_run_state_is_serializable() -> None:
    _state().assert_serializable()


def test_run_state_rejects_a_live_object() -> None:
    """Un cliente, un socket o una corrutina no pueden entrar al estado."""

    class FakeHttpClient:
        pass

    with pytest.raises(ValidationError):
        _state(warnings=[FakeHttpClient()])  # type: ignore[list-item]


def test_run_state_rejects_a_coroutine_in_free_form_data() -> None:
    async def pending() -> None: ...

    coroutine = pending()
    try:
        with pytest.raises(ValidationError):
            _state(attempts={"classify": coroutine})  # type: ignore[dict-item]
    finally:
        coroutine.close()


def test_run_state_rejects_secrets_in_action_parameters() -> None:
    with pytest.raises(ValidationError):
        ActionRequest(
            action_id="act_000001",
            run_id="run_000001",
            tool_name="vehiculos.reservar_cita",
            input_schema_ref="contracts://tools/x.input.v1",
            tool_version="1.0.0",
            expected_version=1,
            parameters={"api_key": "sk-demo"},
            required_permission="appointment:create",
        )


def test_waiting_confirmation_requires_a_persisted_action() -> None:
    with pytest.raises(ValidationError):
        _state(status=RunStatus.WAITING_CONFIRMATION)


def test_failed_run_requires_a_normalized_error() -> None:
    with pytest.raises(ValidationError):
        _state(status=RunStatus.FAILED)


# --- Escrituras (`DIE-F0-017`, §7.8) ----------------------------------------


def _write_tool(**overrides) -> ToolMetadata:
    payload = {
        "name": "vehiculos.reservar_cita",
        "version": "1.0.0",
        "domain": Domain.VEHICULOS,
        "mode": ToolMode.WRITE,
        "allowed_roles": ["citizen"],
        "requires_confirmation": True,
        "requires_idempotency_key": True,
        "input_schema_ref": "contracts://tools/x.input.v1",
        "output_schema_ref": "contracts://tools/x.output.v1",
    }
    payload.update(overrides)
    return ToolMetadata(**payload)


def test_write_tool_without_confirmation_is_rejected() -> None:
    with pytest.raises(ValidationError, match="confirmación"):
        _write_tool(requires_confirmation=False)


def test_write_tool_without_idempotency_is_rejected() -> None:
    with pytest.raises(ValidationError, match="idempotency_key"):
        _write_tool(requires_idempotency_key=False)


def test_write_tool_cannot_declare_automatic_retries() -> None:
    with pytest.raises(ValidationError, match="nunca se reintenta"):
        _write_tool(max_attempts=3)


def test_write_call_requires_consent_and_idempotency_key() -> None:
    context = ToolPermissionContext(
        user_id="usr_demo", institution_id="inst_demo", roles=["citizen"]
    )
    with pytest.raises(ValidationError):
        ToolCall(
            tool_call_id="tc_000001",
            name="vehiculos.reservar_cita",
            version="1.0.0",
            run_id="run_000001",
            trace_id="trace_000001",
            context=context,
            parameters={},
            mode=ToolMode.WRITE,
        )


def test_confirmed_action_without_consent_is_rejected() -> None:
    with pytest.raises(ValidationError, match="consentimiento"):
        ActionRequest(
            action_id="act_000001",
            run_id="run_000001",
            tool_name="vehiculos.reservar_cita",
            input_schema_ref="contracts://tools/x.input.v1",
            tool_version="1.0.0",
            expected_version=1,
            required_permission="appointment:create",
            status=ActionStatus.CONFIRMED,
            consent=False,
            idempotency_key="824a2b5c-1389-4ef5-a346-b00270fd1b42",
        )


def test_only_the_transactional_agent_may_propose_writes() -> None:
    write_proposal = ProposedToolCall(
        name="vehiculos.reservar_cita",
        mode=ToolMode.WRITE,
        rationale="quiere reservar",
        parameters={},
    )
    with pytest.raises(ValidationError, match="transaccional"):
        AgentResult(
            task_id="task_000001",
            agent=AgentName.DOMAIN_NAVIGATOR,
            status=TaskStatus.SUCCEEDED,
            proposed_tools=[write_proposal],
            self_check=SelfCheckResult(schema_valid=True),
        )

    allowed = AgentResult(
        task_id="task_000001",
        agent=AgentName.TRANSACTIONAL,
        status=TaskStatus.SUCCEEDED,
        proposed_tools=[write_proposal],
        self_check=SelfCheckResult(schema_valid=True),
    )
    assert allowed.proposed_tools[0].mode is ToolMode.WRITE


def test_unknown_outcome_is_never_retryable() -> None:
    with pytest.raises(ValidationError, match="outcome desconocido"):
        NormalizedError(
            code=ErrorCode.UNKNOWN_OUTCOME,
            message="no sabemos si se aplicó",
            retryable=True,
            outcome=Outcome.UNKNOWN,
        )


def test_from_code_never_marks_unknown_outcomes_retryable() -> None:
    error = NormalizedError.from_code(ErrorCode.TOOL_TIMEOUT, "timeout", outcome=Outcome.UNKNOWN)
    assert error.retryable is False


# --- Evidencia (`DIE-F0-016`) ------------------------------------------------


def _critical_fact(**overrides) -> VerifiedFact:
    payload = {
        "fact_id": "fact_cost_01",
        "claim": "El costo es 1,250.00 MXN.",
        "value": FactValue(money=Money(amount_minor=125000, currency="MXN")),
        "category": FactCategory.COST,
        "domain": Domain.VEHICULOS,
        "verification": VerificationStatus.ACCEPTED,
        "reason": "citation_supports_claim",
        "confidence": 0.9,
        "citations": [LICENSE_CITATION],
    }
    payload.update(overrides)
    return VerifiedFact(**payload)


def test_critical_accepted_fact_requires_evidence() -> None:
    with pytest.raises(ValidationError, match="sin evidencia activa"):
        _critical_fact(citations=[])


def test_expired_citation_does_not_support_a_critical_fact() -> None:
    expired = LICENSE_CITATION.model_copy(update={"is_active": False})
    with pytest.raises(ValidationError, match="sin evidencia activa"):
        _critical_fact(citations=[expired])


def test_a_tool_call_is_the_other_admissible_evidence() -> None:
    """La evidencia admisible es de dos clases, no una.

    Exigir siempre citación documental hacía **inexpresable** el caso más
    importante del sistema —«la cita quedó reservada, folio NEXO-MOCK-01»—,
    porque `ACTION_RESULT` es crítico por definición y jamás procede de un
    documento. Lo detectó el verificador al construirlo (F1.6).
    """
    fact = _critical_fact(citations=[], supporting_tool_call_id="tc_01")

    assert fact.is_critical is True
    assert fact.has_active_evidence is True


def test_neither_kind_of_evidence_still_fails() -> None:
    """Lo que no cambia: sin ninguna de las dos, no hay aceptación."""
    with pytest.raises(ValidationError, match="sin evidencia activa"):
        _critical_fact(citations=[], supporting_tool_call_id=None)


def test_non_critical_fact_may_lack_citations() -> None:
    """Orientación y contexto no exigen citación; requisitos y costos sí."""
    fact = _critical_fact(
        fact_id="fact_ctx_01",
        category=FactCategory.CONTEXT,
        value=FactValue(text="La persona está en Durango."),
        citations=[],
    )
    assert fact.is_critical is False


def test_write_eligibility_requires_acceptance() -> None:
    with pytest.raises(ValidationError, match="write_eligible"):
        _critical_fact(verification=VerificationStatus.UNCERTAIN, write_eligible=True)


def test_verified_facts_is_immutable() -> None:
    snapshot = VerifiedFacts(snapshot_id="snap_1", created_at=NOW, facts=(_critical_fact(),))
    with pytest.raises(ValidationError):
        snapshot.snapshot_id = "otro"  # type: ignore[misc]


def test_accepted_fact_cannot_depend_on_a_rejected_one() -> None:
    rejected = _critical_fact(
        fact_id="fact_req_01",
        category=FactCategory.REQUIREMENT,
        verification=VerificationStatus.REJECTED,
        reason="source_expired",
    )
    dependent = _critical_fact(depends_on=["fact_req_01"])
    with pytest.raises(ValidationError, match="depende de hechos rechazados"):
        VerifiedFacts(snapshot_id="snap_1", created_at=NOW, facts=(rejected, dependent))


def test_dependencies_must_exist_in_the_snapshot() -> None:
    with pytest.raises(ValidationError, match="dependencias ausentes"):
        VerifiedFacts(
            snapshot_id="snap_1",
            created_at=NOW,
            facts=(_critical_fact(depends_on=["fact_inexistente"]),),
        )


def test_rag_candidate_fact_requires_a_citation() -> None:
    with pytest.raises(ValidationError, match="al menos una citación"):
        CandidateFact(
            fact_id="fact_x",
            claim="algo",
            value=FactValue(text="algo"),
            category=FactCategory.REQUIREMENT,
            domain=Domain.VEHICULOS,
            origin=FactOrigin.RAG,
            confidence=0.5,
        )


# --- Proyección a RunResult (`DIE-F0-044`) ----------------------------------


def test_run_result_never_exposes_internal_state() -> None:
    from nexo_contracts import RunResult

    state = _state(
        candidate_facts=[
            CandidateFact(
                fact_id="fact_borrador",
                claim="sin verificar",
                value=FactValue(text="x"),
                category=FactCategory.CONTEXT,
                domain=Domain.VEHICULOS,
                origin=FactOrigin.USER,
                confidence=0.1,
            )
        ],
        completed_nodes=["start", "classify_fake"],
        attempts={"classify_fake": 2},
    )
    result = RunResult.from_state(state)
    payload = result.model_dump_json()
    assert "fact_borrador" not in payload
    assert "completed_nodes" not in payload
    assert "attempts" not in payload
