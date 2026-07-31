"""Replay estable para grafo/timeline desde eventos (`DIE-F2-056`–`062`)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from nexo_contracts import (
    EventSequence,
    EventStatus,
    EventType,
    EventVisibility,
    NexoModel,
    RunEvent,
    SafePayload,
)

EVENT_FAMILY_KIND: dict[str, str] = {
    "run": "run",
    "classification": "agent",
    "plan": "supervisor",
    "agent": "agent",
    "rag": "retriever",
    "tool": "tool",
    "model": "model",
    "verification": "verifier",
    "contradiction": "verifier",
    "checkpoint": "checkpoint",
    "a2ui": "a2ui",
    "evaluation": "evaluation",
}


class PublicWorkflowEvent(NexoModel):
    event_id: str
    sequence: int
    type: EventType
    status: EventStatus
    actor_type: str
    actor_name: str
    timestamp: str
    duration_ms: int | None = None
    parent_event_id: str | None = None
    correlation_id: str
    data: SafePayload = Field(default_factory=dict)


class WorkflowNode(NexoModel):
    node_id: str
    label: str
    kind: str
    status: EventStatus
    started_sequence: int
    completed_sequence: int | None = None
    duration_ms: int | None = None


class WorkflowEdge(NexoModel):
    source: str
    target: str


class WorkflowReplay(NexoModel):
    mapping_version: str = "workflow-event-mapping-v1"
    run_id: str
    correlation_id: str
    last_sequence: int
    final_event_type: EventType
    catalog_version: str | None = None
    skill_id: str | None = None
    skill_version: str | None = None
    nodes: Annotated[list[WorkflowNode], Field(max_length=10_000)]
    edges: Annotated[list[WorkflowEdge], Field(max_length=20_000)]
    timeline: Annotated[list[PublicWorkflowEvent], Field(max_length=10_000)]


def public_event(event: RunEvent) -> PublicWorkflowEvent:
    """Proyecta un evento sin exponer el payload restringido de auditoría."""
    restricted = event.visibility is EventVisibility.RESTRICTED
    return PublicWorkflowEvent(
        event_id=event.event_id,
        sequence=event.sequence,
        type=event.type,
        status=event.status,
        actor_type=event.actor.type.value,
        actor_name="restringido" if restricted else event.actor.name,
        timestamp=event.timestamp.isoformat(),
        duration_ms=event.duration_ms,
        parent_event_id=event.parent_event_id,
        correlation_id=event.correlation_id,
        data=event.public_data,
    )


def replay_workflow(events: list[RunEvent]) -> WorkflowReplay:
    """Reconstruye el workflow usando únicamente la secuencia de eventos."""
    if not events:
        raise ValueError("el replay requiere al menos un evento")
    sequence = EventSequence(run_id=events[0].run_id, events=events)
    seen_events: set[str] = set()
    for event in sequence.events:
        if event.parent_event_id is not None and event.parent_event_id not in seen_events:
            raise ValueError(
                f"el evento {event.event_id!r} apunta a un parent_event_id futuro o inexistente"
            )
        seen_events.add(event.event_id)

    nodes: dict[str, WorkflowNode] = {}
    edges: list[WorkflowEdge] = []
    current_node: str | None = None
    last_node: str | None = None

    for event in sequence.events:
        node_name = event.data.get("node")
        if event.type is EventType.AGENT_STARTED and isinstance(node_name, str):
            current_node = node_name
            nodes[node_name] = WorkflowNode(
                node_id=node_name,
                label=node_name,
                kind="agent",
                status=event.status,
                started_sequence=event.sequence,
            )
            if last_node is not None and last_node != node_name:
                edges.append(WorkflowEdge(source=last_node, target=node_name))
            last_node = node_name
            continue

        if event.type in {EventType.AGENT_COMPLETED, EventType.AGENT_FAILED} and isinstance(
            node_name, str
        ):
            existing = nodes.get(node_name)
            if existing is not None:
                nodes[node_name] = existing.model_copy(
                    update={
                        "status": event.status,
                        "completed_sequence": event.sequence,
                        "duration_ms": event.duration_ms,
                    }
                )
            current_node = None
            continue

        family = event.type.value.split(".", 1)[0]
        kind = EVENT_FAMILY_KIND.get(family)
        if kind in {"retriever", "tool", "model", "a2ui"}:
            subsystem_id = event.event_id
            nodes[subsystem_id] = WorkflowNode(
                node_id=subsystem_id,
                label=event.type.value,
                kind=kind,
                status=event.status,
                started_sequence=event.sequence,
                completed_sequence=event.sequence,
                duration_ms=event.duration_ms,
            )
            if current_node is not None:
                edges.append(WorkflowEdge(source=current_node, target=subsystem_id))

    final = sequence.events[-1]
    return WorkflowReplay(
        run_id=sequence.run_id,
        correlation_id=final.correlation_id,
        last_sequence=sequence.last_sequence,
        final_event_type=final.type,
        catalog_version=final.catalog_version,
        skill_id=final.skill_id,
        skill_version=final.skill_version,
        nodes=list(nodes.values()),
        edges=_unique_edges(edges),
        timeline=[public_event(event) for event in sequence.events],
    )


def _unique_edges(edges: list[WorkflowEdge]) -> list[WorkflowEdge]:
    seen: set[tuple[str, str]] = set()
    unique: list[WorkflowEdge] = []
    for edge in edges:
        key = (edge.source, edge.target)
        if key not in seen:
            seen.add(key)
            unique.append(edge)
    return unique


__all__ = [
    "EVENT_FAMILY_KIND",
    "PublicWorkflowEvent",
    "WorkflowEdge",
    "WorkflowNode",
    "WorkflowReplay",
    "public_event",
    "replay_workflow",
]
