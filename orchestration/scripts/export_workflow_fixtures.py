"""Genera fixtures de replay Core para backend y renderer web."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from nexo_contracts import (
    ActorType,
    ErrorCode,
    EventActor,
    EventStatus,
    EventType,
    EventVisibility,
    NormalizedError,
    RunEvent,
)
from nexo_orchestration.workflow import replay_workflow

NOW = datetime(2026, 7, 30, 15, 0, tzinfo=UTC)


def _events(
    run_id: str,
    specs: list[tuple[EventType, EventStatus, ActorType, str, dict[str, object], bool]],
) -> list[RunEvent]:
    events: list[RunEvent] = []
    for sequence, (event_type, status, actor_type, actor_name, data, failed) in enumerate(
        specs, start=1
    ):
        error = (
            NormalizedError.from_code(
                ErrorCode.PERMISSION_DENIED
                if event_type is EventType.TOOL_DENIED
                else ErrorCode.PROVIDER_ERROR,
                "La operación no pudo completarse de forma segura.",
            )
            if failed
            else None
        )
        event_id = f"evt_{run_id.removeprefix('run_')}_{sequence:03d}"
        events.append(
            RunEvent(
                event_id=event_id,
                trace_id=f"trace_{run_id.removeprefix('run_')}",
                run_id=run_id,
                sequence=sequence,
                type=event_type,
                timestamp=NOW,
                actor=EventActor(type=actor_type, name=actor_name),
                status=status,
                visibility=(
                    EventVisibility.RESTRICTED
                    if actor_type is ActorType.MODEL
                    else EventVisibility.PUBLIC
                ),
                correlation_id=f"trace_{run_id.removeprefix('run_')}",
                parent_event_id=events[-1].event_id if events else None,
                duration_ms=12 if event_type.value.endswith(("completed", "failed")) else None,
                data=data,
                public_data={
                    key: value
                    for key, value in data.items()
                    if key in {"node", "reason", "attempt", "outcome"}
                },
                error=error,
                policy_version="policies-2026-07-30",
                catalog_version="core-catalog-2026-07-30",
                skill_id="skill_sal_navegacion",
                skill_version="1.0.0",
            )
        )
    return events


def _fixtures() -> dict[str, list[RunEvent]]:
    return {
        "success": _events(
            "run_wf_success",
            [
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "classify",
                    {"node": "classify"},
                    False,
                ),
                (
                    EventType.MODEL_SELECTED,
                    EventStatus.SUCCEEDED,
                    ActorType.MODEL,
                    "general",
                    {"attempt": 1, "outcome": "selected"},
                    False,
                ),
                (
                    EventType.MODEL_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.MODEL,
                    "general",
                    {"attempt": 1, "outcome": "schema_valid"},
                    False,
                ),
                (
                    EventType.AGENT_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "classify",
                    {"node": "classify"},
                    False,
                ),
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "retrieve",
                    {"node": "retrieve"},
                    False,
                ),
                (
                    EventType.RAG_STARTED,
                    EventStatus.STARTED,
                    ActorType.RETRIEVER,
                    "hybrid_retriever",
                    {"outcome": "started"},
                    False,
                ),
                (
                    EventType.RAG_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.RETRIEVER,
                    "hybrid_retriever",
                    {"outcome": "evidence_found"},
                    False,
                ),
                (
                    EventType.AGENT_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "retrieve",
                    {"node": "retrieve"},
                    False,
                ),
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "read_tools",
                    {"node": "read_tools"},
                    False,
                ),
                (
                    EventType.TOOL_REQUESTED,
                    EventStatus.STARTED,
                    ActorType.AGENT,
                    "domain_navigator",
                    {"outcome": "requested"},
                    False,
                ),
                (
                    EventType.TOOL_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.TOOL,
                    "salud.localizar_unidad_salud",
                    {"outcome": "known_success"},
                    False,
                ),
                (
                    EventType.AGENT_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "read_tools",
                    {"node": "read_tools"},
                    False,
                ),
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "verify",
                    {"node": "verify"},
                    False,
                ),
                (
                    EventType.VERIFICATION_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.AGENT,
                    "verifier",
                    {"outcome": "accepted"},
                    False,
                ),
                (
                    EventType.AGENT_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "verify",
                    {"node": "verify"},
                    False,
                ),
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "build_a2ui",
                    {"node": "build_a2ui"},
                    False,
                ),
                (
                    EventType.A2UI_VALIDATED,
                    EventStatus.SUCCEEDED,
                    ActorType.SYSTEM,
                    "a2ui_validator",
                    {"outcome": "valid"},
                    False,
                ),
                (
                    EventType.AGENT_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "build_a2ui",
                    {"node": "build_a2ui"},
                    False,
                ),
                (
                    EventType.RUN_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "supervisor",
                    {"outcome": "succeeded"},
                    False,
                ),
            ],
        ),
        "partial": _events(
            "run_wf_partial",
            [
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "navigate",
                    {"node": "navigate"},
                    False,
                ),
                (
                    EventType.AGENT_FAILED,
                    EventStatus.FAILED,
                    ActorType.SUPERVISOR,
                    "navigate",
                    {"node": "navigate", "outcome": "partial"},
                    True,
                ),
                (
                    EventType.RUN_PARTIAL,
                    EventStatus.FAILED,
                    ActorType.SUPERVISOR,
                    "supervisor",
                    {"outcome": "partial"},
                    True,
                ),
            ],
        ),
        "retry": _events(
            "run_wf_retry",
            [
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "classify",
                    {"node": "classify"},
                    False,
                ),
                (
                    EventType.AGENT_RETRIED,
                    EventStatus.STARTED,
                    ActorType.MODEL,
                    "general",
                    {"attempt": 2, "reason": "invalid_schema"},
                    False,
                ),
                (
                    EventType.MODEL_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.MODEL,
                    "general",
                    {"attempt": 2, "outcome": "schema_valid"},
                    False,
                ),
                (
                    EventType.AGENT_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "classify",
                    {"node": "classify"},
                    False,
                ),
                (
                    EventType.RUN_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "supervisor",
                    {"outcome": "succeeded"},
                    False,
                ),
            ],
        ),
        "permission_denied": _events(
            "run_wf_denied",
            [
                (
                    EventType.AGENT_STARTED,
                    EventStatus.STARTED,
                    ActorType.SUPERVISOR,
                    "read_tools",
                    {"node": "read_tools"},
                    False,
                ),
                (
                    EventType.TOOL_DENIED,
                    EventStatus.DENIED,
                    ActorType.TOOL,
                    "ganaderia.consultar_animal",
                    {"reason": "no_permission_rule"},
                    True,
                ),
                (
                    EventType.RUN_PARTIAL,
                    EventStatus.FAILED,
                    ActorType.SUPERVISOR,
                    "supervisor",
                    {"outcome": "permission_denied"},
                    True,
                ),
            ],
        ),
        "confirmation": _events(
            "run_wf_confirmation",
            [
                (
                    EventType.RUN_WAITING_CONFIRMATION,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "supervisor",
                    {"outcome": "waiting_confirmation"},
                    False,
                ),
                (
                    EventType.RUN_RESUMED,
                    EventStatus.SUCCEEDED,
                    ActorType.USER,
                    "citizen",
                    {"reason": "explicit_confirmation"},
                    False,
                ),
                (
                    EventType.TOOL_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.TOOL,
                    "registro_civil.registrar_solicitud",
                    {"outcome": "known_success"},
                    False,
                ),
                (
                    EventType.RUN_COMPLETED,
                    EventStatus.SUCCEEDED,
                    ActorType.SUPERVISOR,
                    "supervisor",
                    {"outcome": "succeeded"},
                    False,
                ),
            ],
        ),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    destinations = (
        root / "orchestration/fixtures/workflow",
        root / "apps/web/public/fixtures/workflow",
    )
    for name, events in _fixtures().items():
        replay = replay_workflow(events)
        payload = {
            "events": [event.model_dump(mode="json") for event in events],
            "replay": replay.model_dump(mode="json"),
        }
        rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        for destination in destinations:
            destination.mkdir(parents=True, exist_ok=True)
            (destination / f"{name}.json").write_text(rendered, encoding="utf-8")
    print(f"{len(_fixtures())} fixtures exportados en {len(destinations)} destinos")


if __name__ == "__main__":
    main()
