"""Registry y executor de tools: autorización, desenlaces e idempotencia (§7.8).

El caso central es el outcome desconocido: es el único en el que no sabemos si
la escritura ocurrió, y por tanto el único que nunca puede reintentarse ni
reportarse como éxito.
"""

from __future__ import annotations

import pytest

from nexo_contracts import (
    Domain,
    ErrorCode,
    Outcome,
    RiskLevel,
    ToolCall,
    ToolCallStatus,
    ToolMetadata,
    ToolMode,
    ToolPermissionContext,
)
from nexo_mcp.testing import (
    InMemoryToolExecutor,
    InMemoryToolRegistry,
    ToolBehavior,
    ToolScenario,
)

pytestmark = pytest.mark.unit

IDEMPOTENCY_KEY = "824a2b5c-1389-4ef5-a346-b00270fd1b42"


def _read_tool() -> ToolMetadata:
    return ToolMetadata(
        name="vehiculos.consultar_adeudo",
        version="1.0.0",
        domain=Domain.VEHICULOS,
        mode=ToolMode.READ,
        allowed_roles=["citizen", "operator"],
        input_schema_ref="contracts://tools/adeudo.input.v1",
        output_schema_ref="contracts://tools/adeudo.output.v1",
    )


def _write_tool() -> ToolMetadata:
    return ToolMetadata(
        name="vehiculos.reservar_cita",
        version="1.0.0",
        domain=Domain.VEHICULOS,
        mode=ToolMode.WRITE,
        risk=RiskLevel.MEDIUM,
        allowed_roles=["citizen"],
        requires_confirmation=True,
        requires_idempotency_key=True,
        max_attempts=1,
        input_schema_ref="contracts://tools/cita.input.v1",
        output_schema_ref="contracts://tools/cita.output.v1",
    )


def _context(roles: list[str] | None = None) -> ToolPermissionContext:
    return ToolPermissionContext(
        user_id="usr_demo", institution_id="inst_demo", roles=roles or ["citizen"]
    )


def _read_call(**overrides) -> ToolCall:
    payload = {
        "tool_call_id": "tc_000001",
        "name": "vehiculos.consultar_adeudo",
        "version": "1.0.0",
        "run_id": "run_000001",
        "trace_id": "trace_000001",
        "context": _context(),
        "parameters": {},
        "mode": ToolMode.READ,
    }
    payload.update(overrides)
    return ToolCall(**payload)


def _write_call(**overrides) -> ToolCall:
    payload = {
        "tool_call_id": "tc_000002",
        "name": "vehiculos.reservar_cita",
        "version": "1.0.0",
        "run_id": "run_000001",
        "trace_id": "trace_000001",
        "context": _context(),
        "parameters": {"slot_id": "slot_101"},
        "action_id": "act_000001",
        "idempotency_key": IDEMPOTENCY_KEY,
        "confirmed": True,
        "mode": ToolMode.WRITE,
    }
    payload.update(overrides)
    return ToolCall(**payload)


# --- Registry ----------------------------------------------------------------


async def test_registry_hides_tools_outside_the_actor_role() -> None:
    registry = InMemoryToolRegistry([_write_tool()])
    visible = await registry.list_tools(institution_id="inst_demo", roles=["auditor"])
    assert visible == ()


async def test_registry_filters_by_institution() -> None:
    registry = InMemoryToolRegistry()
    registry.register(_read_tool(), institution_id="inst_otra")
    assert await registry.list_tools(institution_id="inst_demo", roles=["citizen"]) == ()


async def test_registry_filters_by_domain() -> None:
    registry = InMemoryToolRegistry([_read_tool()])
    assert await registry.list_tools(
        institution_id="inst_demo", roles=["citizen"], domain="salud"
    ) == ()


async def test_registry_refuses_to_replace_a_published_version() -> None:
    registry = InMemoryToolRegistry([_read_tool()])
    with pytest.raises(ValueError, match="ya está registrada"):
        registry.register(_read_tool())


async def test_registry_listing_is_stable() -> None:
    registry = InMemoryToolRegistry([_write_tool(), _read_tool()])
    first = await registry.list_tools(institution_id="inst_demo", roles=["citizen"])
    second = await registry.list_tools(institution_id="inst_demo", roles=["citizen"])
    assert [tool.name for tool in first] == [tool.name for tool in second]


# --- Executor: desenlaces ----------------------------------------------------


async def test_successful_read_returns_typed_data() -> None:
    registry = InMemoryToolRegistry([_read_tool()])
    executor = InMemoryToolExecutor(
        registry,
        {"vehiculos.consultar_adeudo": ToolScenario(data={"amount_minor": 0})},
    )
    result = await executor.execute(_read_call())
    assert result.status is ToolCallStatus.SUCCEEDED
    assert result.data == {"amount_minor": 0}
    assert result.error is None


@pytest.mark.parametrize(
    ("behavior", "code", "status"),
    [
        (ToolBehavior.TIMEOUT, ErrorCode.TOOL_TIMEOUT, ToolCallStatus.TIMEOUT),
        (ToolBehavior.SCHEMA_ERROR, ErrorCode.VALIDATION_ERROR, ToolCallStatus.FAILED),
        (
            ToolBehavior.PERMISSION_DENIED,
            ErrorCode.PERMISSION_DENIED,
            ToolCallStatus.DENIED,
        ),
        (ToolBehavior.UNKNOWN_OUTCOME, ErrorCode.UNKNOWN_OUTCOME, ToolCallStatus.FAILED),
    ],
)
async def test_failure_modes_are_normalized(behavior, code, status) -> None:
    registry = InMemoryToolRegistry([_read_tool()])
    executor = InMemoryToolExecutor(
        registry, {"vehiculos.consultar_adeudo": ToolScenario(behavior=behavior)}
    )
    result = await executor.execute(_read_call())
    assert result.status is status
    assert result.error is not None
    assert result.error.code is code


async def test_executor_never_raises_provider_exceptions() -> None:
    """Los fallos viajan dentro de `ToolResult`, no como excepciones."""
    registry = InMemoryToolRegistry([_read_tool()])
    executor = InMemoryToolExecutor(
        registry, {"vehiculos.consultar_adeudo": ToolScenario(behavior=ToolBehavior.TIMEOUT)}
    )
    result = await executor.execute(_read_call())
    assert result.error is not None


async def test_unknown_outcome_is_not_retryable() -> None:
    registry = InMemoryToolRegistry([_read_tool()])
    executor = InMemoryToolExecutor(
        registry,
        {"vehiculos.consultar_adeudo": ToolScenario(behavior=ToolBehavior.UNKNOWN_OUTCOME)},
    )
    result = await executor.execute(_read_call())
    assert result.error is not None
    assert result.error.outcome is Outcome.UNKNOWN
    assert result.error.error.retryable is False


# --- Executor: autorización revalidada ---------------------------------------


@pytest.mark.security
async def test_executor_revalidates_the_role() -> None:
    """No confía en que el supervisor haya filtrado bien."""
    registry = InMemoryToolRegistry([_write_tool()])
    executor = InMemoryToolExecutor(registry)
    result = await executor.execute(_write_call(context=_context(roles=["auditor"])))
    assert result.status is ToolCallStatus.DENIED
    assert result.error is not None
    assert result.error.code is ErrorCode.PERMISSION_DENIED


@pytest.mark.security
async def test_unregistered_tool_is_denied() -> None:
    executor = InMemoryToolExecutor(InMemoryToolRegistry())
    result = await executor.execute(_read_call())
    assert result.status is ToolCallStatus.FAILED
    assert result.error is not None
    assert result.error.code is ErrorCode.RESOURCE_NOT_FOUND


@pytest.mark.security
async def test_unregistered_version_is_denied() -> None:
    """Una versión no registrada no se resuelve a la más parecida."""
    registry = InMemoryToolRegistry([_read_tool()])
    executor = InMemoryToolExecutor(registry)
    result = await executor.execute(_read_call(version="9.9.9"))
    assert result.error is not None
    assert result.error.code is ErrorCode.RESOURCE_NOT_FOUND


@pytest.mark.security
async def test_read_call_cannot_reach_a_write_tool() -> None:
    """Declarar `read` sobre una tool de escritura no la vuelve inocua."""
    registry = InMemoryToolRegistry([_write_tool()])
    executor = InMemoryToolExecutor(registry)
    result = await executor.execute(
        _read_call(name="vehiculos.reservar_cita", mode=ToolMode.READ)
    )
    assert result.status is ToolCallStatus.DENIED


# --- Escrituras: folio e idempotencia ----------------------------------------


async def test_successful_write_returns_a_verifiable_identifier() -> None:
    registry = InMemoryToolRegistry([_write_tool()])
    executor = InMemoryToolExecutor(registry)
    result = await executor.execute(_write_call())

    assert result.status is ToolCallStatus.SUCCEEDED
    assert result.confirmation is not None
    assert result.confirmation.identifier
    assert result.confirmation.is_mock is True


async def test_repeated_confirmation_replays_without_writing_again() -> None:
    """`DIE-F1-080`: confirmar dos veces no crea dos citas."""
    registry = InMemoryToolRegistry([_write_tool()])
    executor = InMemoryToolExecutor(registry)

    first = await executor.execute(_write_call())
    second = await executor.execute(_write_call(tool_call_id="tc_000003"))

    assert second.idempotency_replayed is True
    assert first.confirmation is not None
    assert second.confirmation is not None
    assert second.confirmation.identifier == first.confirmation.identifier


async def test_different_idempotency_keys_produce_different_writes() -> None:
    registry = InMemoryToolRegistry([_write_tool()])
    executor = InMemoryToolExecutor(registry)

    first = await executor.execute(_write_call())
    second = await executor.execute(
        _write_call(
            tool_call_id="tc_000003",
            idempotency_key="9f0c1d2e-3a4b-5c6d-7e8f-901a2b3c4d5e",
        )
    )
    assert second.idempotency_replayed is False
    assert first.confirmation is not None
    assert second.confirmation is not None
    assert first.confirmation.identifier != second.confirmation.identifier


async def test_write_folios_are_reproducible_with_an_injected_clock() -> None:
    from nexo_orchestration.testing import FrozenClock

    registry = InMemoryToolRegistry([_write_tool()])
    executor = InMemoryToolExecutor(registry, clock=FrozenClock())
    result = await executor.execute(_write_call())
    assert result.confirmation is not None
    assert result.confirmation.issued_at.isoformat() == "2026-07-30T15:00:00+00:00"
