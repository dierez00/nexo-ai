"""Resultados MCP convertidos a hechos verificables del MVP."""

from datetime import UTC, datetime

from nexo_agents.tool_facts import project_tool_results
from nexo_contracts import Domain, FactCategory, ToolCallStatus, ToolResult


def _result(name: str, data: dict[str, object]) -> ToolResult:
    return ToolResult(
        tool_call_id="tc_000001",
        name=name,
        status=ToolCallStatus.SUCCEEDED,
        data=data,
        provider="mock",
        duration_ms=1,
        is_mock=True,
    )


def test_vehicle_debt_keeps_the_tool_call_as_evidence() -> None:
    facts = project_tool_results(
        [
            _result(
                "vehiculos.consultar_adeudo",
                {
                    "tiene_adeudo": False,
                    "total": {"amount_minor": 0, "currency": "MXN"},
                    "conceptos": [],
                    "bloquea_renovacion": False,
                },
            )
        ],
        Domain.VEHICULOS,
    )

    assert {fact.category for fact in facts} == {
        FactCategory.COST,
        FactCategory.CONTEXT,
    }
    assert all(fact.tool_call_id == "tc_000001" for fact in facts)


def test_available_slots_become_schedule_facts() -> None:
    facts = project_tool_results(
        [
            _result(
                "vehiculos.buscar_citas",
                {
                    "slots": [
                        {
                            "slot_id": "slot_01",
                            "inicio": datetime(2026, 8, 3, 9, tzinfo=UTC).isoformat(),
                            "disponible": True,
                        }
                    ],
                    "version_catalogo": "citas-v1",
                },
            )
        ],
        Domain.VEHICULOS,
    )

    assert len(facts) == 1
    assert facts[0].category is FactCategory.SCHEDULE
    assert facts[0].value.items == ["2026-08-03T09:00:00+00:00 · slot_01"]


def test_failed_tools_do_not_create_facts() -> None:
    result = _result("vehiculos.localizar_modulo", {"modulos": []}).model_copy(
        update={
            "status": ToolCallStatus.FAILED,
            "error": {
                "error": {
                    "code": "provider_error",
                    "message": "falló",
                    "retryable": True,
                    "outcome": "known_failure",
                },
                "provider": "mock",
                "safe_details": {},
            },
        }
    )

    assert project_tool_results([result], Domain.VEHICULOS) == ()
