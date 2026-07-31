"""Agente transaccional: la única puerta a una escritura (F1.10)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from nexo_agents.transactional import TransactionalAgent
from nexo_contracts import (
    ActionRequest,
    ActionStatus,
    Contradiction,
    ContradictionSeverity,
    ErrorCode,
    FactCategory,
    FactValue,
    Money,
    Outcome,
    SourceCitation,
    ToolPermissionContext,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_mcp.authorization import PermissionMatrix
from nexo_mcp.catalog import ToolCatalog
from nexo_mcp.execution import AdapterFailure, ToolExecutor
from nexo_orchestration.configuration import load_config

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)
IDEMPOTENCY_KEY = "824a2b5c-1389-4ef5-a346-b00270fd1b42"

CITIZEN = ToolPermissionContext(user_id="usr_demo", institution_id="inst_demo", roles=["citizen"])

CITATION = SourceCitation(
    source_id="src_veh_tarifas",
    fragment_id="frag_costos",
    corpus_version="vehiculos-2026-07-30",
    source_version="v2",
    valid_from=date(2026, 1, 1),
    is_active=True,
)


@pytest.fixture(scope="module")
def config():
    return load_config()


@pytest.fixture
def catalog(config) -> ToolCatalog:
    return ToolCatalog(
        config=config.tool_registry, permissions=PermissionMatrix(config=config.permissions)
    )


@pytest.fixture
def executor(catalog, config) -> ToolExecutor:
    return ToolExecutor(catalog=catalog, permissions=PermissionMatrix(config=config.permissions))


@pytest.fixture
def agent(catalog, executor) -> TransactionalAgent:
    return TransactionalAgent(catalog=catalog, executor=executor)


@pytest.fixture
def facts() -> VerifiedFacts:
    return VerifiedFacts(
        snapshot_id="snapshot_cap_veh_01",
        created_at=NOW,
        facts=(
            VerifiedFact(
                fact_id="fact_cost_01",
                claim="La renovación a tres años cuesta 814.00 MXN.",
                value=FactValue(money=Money(amount_minor=81400, currency="MXN")),
                category=FactCategory.COST,
                domain="vehiculos",  # type: ignore[arg-type]
                verification=VerificationStatus.ACCEPTED,
                reason="citation_supports_claim",
                confidence=0.97,
                citations=[CITATION],
                write_eligible=True,
            ),
        ),
    )


def _action(**overrides: object) -> ActionRequest:
    payload: dict[str, object] = {
        "action_id": "act_reserve_01",
        "run_id": "run_000001",
        "tool_name": "vehiculos.reservar_cita",
        "input_schema_ref": "contracts://tools/vehiculos.reservar_cita.input.v1",
        "tool_version": "1.0.0",
        "expected_version": 1,
        "parameters": {"slot_id": "slot_mod_centro_00", "vehiculo_ref": "veh_demo"},
        "requires_confirmation": True,
        "consent": True,
        "idempotency_key": IDEMPOTENCY_KEY,
        "required_permission": "appointment:create",
        "status": ActionStatus.CONFIRMED,
        "supporting_fact_ids": ["fact_cost_01"],
    }
    payload.update(overrides)
    return ActionRequest(**payload)  # type: ignore[arg-type]


async def _execute(agent, action, facts, *, tool_call_id: str = "tc_01"):
    return await agent.execute(
        action,
        facts=facts,
        identity=CITIZEN,
        tool_call_id=tool_call_id,
        run_id="run_000001",
        trace_id="trace_000001",
    )


# --- Camino feliz (`DIE-F1-078`, `DIE-F1-079`) ------------------------------


async def test_a_confirmed_action_succeeds_with_a_verifiable_folio(agent, facts) -> None:
    outcome = await _execute(agent, _action(), facts)

    assert outcome.succeeded
    assert outcome.action_result.tool_result is not None
    confirmation = outcome.action_result.tool_result.confirmation
    assert confirmation is not None
    assert confirmation.identifier.startswith("NEXO-MOCK-")


async def test_the_mock_nature_is_declared_visibly(agent, facts) -> None:
    """`DIE-F1-079`: nadie debe confundir un folio de demo con uno real."""
    outcome = await _execute(agent, _action(), facts)

    assert any("demostración" in warning for warning in outcome.warnings)


# --- Precondiciones revalidadas (`DIE-F1-073`, `DIE-F1-074`) ---------------


@pytest.mark.security
async def test_an_unconfirmed_action_is_refused(agent, facts) -> None:
    outcome = await _execute(
        agent, _action(status=ActionStatus.PENDING_CONFIRMATION, consent=False), facts
    )

    assert outcome.action_result.status is ActionStatus.FAILED
    assert outcome.action_result.error is not None
    assert outcome.action_result.error.code is ErrorCode.ACTION_CONFIRMATION_REQUIRED
    assert outcome.tool_result is None


@pytest.mark.security
async def test_a_stale_tool_version_is_refused(agent, facts) -> None:
    """Entre persistir la acción y confirmarla pueden haber pasado horas."""
    outcome = await _execute(agent, _action(tool_version="0.9.0"), facts)

    assert outcome.action_result.error is not None
    assert outcome.action_result.error.code is ErrorCode.VERSION_CONFLICT


@pytest.mark.security
async def test_a_non_write_tool_is_refused(agent, facts) -> None:
    """`DIE-F1-075`: el transaccional no ejecuta lecturas.

    No sería peligroso, pero difuminaría la frontera que hace auditable el
    sistema: si puede hacer cualquier cosa, «solo el transaccional escribe»
    deja de significar algo.
    """
    outcome = await _execute(
        agent,
        _action(
            tool_name="vehiculos.consultar_adeudo",
            input_schema_ref="contracts://tools/vehiculos.consultar_adeudo.input.v1",
            parameters={"vehiculo_ref": "veh_demo"},
        ),
        facts,
    )

    assert outcome.action_result.error is not None
    assert outcome.action_result.error.code is ErrorCode.PERMISSION_DENIED
    assert outcome.tool_result is None


@pytest.mark.security
async def test_an_unregistered_tool_is_refused(agent, facts) -> None:
    outcome = await _execute(agent, _action(tool_name="vehiculos.tool_fantasma"), facts)

    assert outcome.action_result.error is not None
    assert outcome.action_result.error.code is ErrorCode.TOOL_NOT_FOUND


@pytest.mark.security
async def test_a_blocking_contradiction_stops_the_write(agent, facts) -> None:
    """Aunque todo lo demás esté en orden (§8 de las convenciones)."""
    blocked = facts.model_copy(
        update={
            "contradictions": (
                Contradiction(
                    contradiction_id="contra_01",
                    fact_ids=["fact_cost_01", "fact_cost_02"],
                    severity=ContradictionSeverity.CRITICAL,
                    rule="document_and_tool_disagree",
                    explanation="el documento y la tool discrepan sobre el costo",
                ),
            )
        }
    )

    outcome = await _execute(agent, _action(), blocked)

    assert outcome.action_result.error is not None
    assert outcome.action_result.error.code is ErrorCode.PERMISSION_DENIED
    assert outcome.tool_result is None


@pytest.mark.security
async def test_an_action_resting_on_a_rejected_fact_is_refused(agent) -> None:
    """El verificador pudo rechazar el hecho después de que se confirmara."""
    rejected = VerifiedFacts(
        snapshot_id="s",
        created_at=NOW,
        facts=(
            VerifiedFact(
                fact_id="fact_cost_01",
                claim="La renovación cuesta 814.00 MXN.",
                value=FactValue(money=Money(amount_minor=81400, currency="MXN")),
                category=FactCategory.COST,
                domain="vehiculos",  # type: ignore[arg-type]
                verification=VerificationStatus.REJECTED,
                reason="source_expired",
                confidence=0.3,
            ),
        ),
    )

    outcome = await _execute(agent, _action(), rejected)

    assert outcome.action_result.error is not None
    assert "ya no sustentan una escritura" in outcome.action_result.error.message


# --- Outcome desconocido (`DIE-F1-077`, `DIE-F1-081`) ----------------------


@pytest.mark.security
async def test_an_unknown_outcome_produces_partial_and_is_never_retried(
    catalog, config, facts
) -> None:
    """Es exactamente cómo se duplica una cita."""
    executor = ToolExecutor(
        catalog=catalog,
        permissions=PermissionMatrix(config=config.permissions),
        failures={
            "vehiculos.reservar_cita": AdapterFailure(
                ErrorCode.UNKNOWN_OUTCOME,
                "se perdió la conexión tras enviar la operación",
                outcome=Outcome.UNKNOWN,
            )
        },
    )
    agent = TransactionalAgent(catalog=catalog, executor=executor)

    outcome = await _execute(agent, _action(), facts)

    assert outcome.is_partial
    assert len(executor.calls) == 1, "una escritura con outcome desconocido no se reintenta"
    assert any("No la repetimos" in warning for warning in outcome.warnings)


@pytest.mark.security
async def test_a_success_without_a_folio_is_reported_as_partial(
    catalog, config, facts, monkeypatch
) -> None:
    """`DIE-F1-078`: la tool dijo que sí y no trajo folio. No es éxito."""
    executor = ToolExecutor(
        catalog=catalog, permissions=PermissionMatrix(config=config.permissions)
    )
    agent = TransactionalAgent(catalog=catalog, executor=executor)

    original = executor._invoke_once

    async def _without_confirmation(call, definition):  # type: ignore[no-untyped-def]
        result = await original(call, definition)
        return result.model_copy(update={"confirmation": None})

    monkeypatch.setattr(executor, "_invoke_once", _without_confirmation)

    outcome = await _execute(agent, _action(), facts)

    assert outcome.is_partial
    assert outcome.action_result.error is not None
    assert outcome.action_result.error.code is ErrorCode.UNKNOWN_OUTCOME


# --- Idempotencia (`DIE-F1-076`, `DIE-F1-080`) -----------------------------


async def test_repeating_the_confirmation_does_not_create_a_second_appointment(
    agent, executor, facts
) -> None:
    first = await _execute(agent, _action(), facts, tool_call_id="tc_01")
    second = await _execute(agent, _action(), facts, tool_call_id="tc_02")

    assert first.succeeded and second.succeeded
    assert second.action_result.idempotency_replayed is True
    assert any("ya se había procesado" in warning for warning in second.warnings)

    first_result = first.action_result.tool_result
    second_result = second.action_result.tool_result
    assert first_result is not None and second_result is not None
    assert first_result.confirmation == second_result.confirmation


async def test_exactly_one_tool_runs_per_confirmed_action(agent, executor, facts) -> None:
    """`DIE-F1-076`: dos escrituras bajo un consentimiento son una de más."""
    await _execute(agent, _action(), facts)

    assert len(executor.calls) == 1


# --- Auditoría (`DIE-F1-082`) ----------------------------------------------


@pytest.mark.security
async def test_the_audit_record_carries_no_parameters(agent, facts) -> None:
    outcome = await _execute(agent, _action(), facts)

    assert outcome.audit is not None
    assert "slot_mod_centro_00" not in str(outcome.audit)
    assert outcome.audit["mode"] == "write"
    assert outcome.audit["confirmed"] is True
    assert outcome.audit["has_idempotency_key"] is True
