import json
from datetime import UTC, datetime
from pathlib import Path

from nexo_contracts import (
    ActorType,
    EventActor,
    EventStatus,
    EventType,
    EventVisibility,
    RunEvent,
)
from nexo_orchestration.workflow import public_event, replay_workflow

NOW = datetime(2026, 7, 30, 15, 0, tzinfo=UTC)


def _event(
    sequence: int,
    event_type: EventType,
    status: EventStatus,
    *,
    node: str | None = None,
    parent: str | None = None,
    visibility: EventVisibility = EventVisibility.PUBLIC,
) -> RunEvent:
    data = {"node": node} if node else {"provider_detail": "interno"}
    return RunEvent(
        event_id=f"evt_{sequence:06d}",
        trace_id="trace_000001",
        run_id="run_000001",
        sequence=sequence,
        type=event_type,
        timestamp=NOW,
        actor=EventActor(type=ActorType.SUPERVISOR, name=node or "interno"),
        status=status,
        visibility=visibility,
        correlation_id="trace_000001",
        parent_event_id=parent,
        data=data,
        public_data={"node": node} if node else {"outcome": status.value},
        catalog_version="core-catalog-2026-07-30",
        skill_id="skill_sal_navegacion",
        skill_version="1.0.0",
    )


def test_replay_reconstructs_nodes_and_subsystems_from_events_only() -> None:
    events = [
        _event(1, EventType.AGENT_STARTED, EventStatus.STARTED, node="retrieve"),
        _event(
            2,
            EventType.RAG_COMPLETED,
            EventStatus.SUCCEEDED,
            parent="evt_000001",
        ),
        _event(
            3,
            EventType.AGENT_COMPLETED,
            EventStatus.SUCCEEDED,
            node="retrieve",
            parent="evt_000002",
        ),
        _event(
            4,
            EventType.RUN_COMPLETED,
            EventStatus.SUCCEEDED,
            parent="evt_000003",
        ),
    ]

    replay = replay_workflow(events)

    assert replay.last_sequence == 4
    assert replay.catalog_version == "core-catalog-2026-07-30"
    assert {node.kind for node in replay.nodes} == {"agent", "retriever"}
    assert replay.edges[0].source == "retrieve"


def test_public_projection_does_not_expose_restricted_audit_data() -> None:
    event = _event(
        1,
        EventType.MODEL_SELECTED,
        EventStatus.SUCCEEDED,
        visibility=EventVisibility.RESTRICTED,
    )

    projected = public_event(event)

    assert projected.actor_name == "restringido"
    assert "provider_detail" not in projected.data
    assert projected.data == {"outcome": "succeeded"}


def test_published_fixtures_replay_to_the_stored_projection() -> None:
    root = Path(__file__).resolve().parents[2]
    fixture_dir = root / "orchestration/fixtures/workflow"

    assert {path.stem for path in fixture_dir.glob("*.json")} == {
        "success",
        "partial",
        "retry",
        "permission_denied",
        "confirmation",
    }
    for path in fixture_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        events = [RunEvent.model_validate(item) for item in payload["events"]]

        assert replay_workflow(events).model_dump(mode="json") == payload["replay"]
