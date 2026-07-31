"""Casos de uso de runs: postear mensaje→ejecutar run, y snapshot."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import RowMapping

from nexo_api.core import ids
from nexo_api.core.errors import ProblemException
from nexo_api.repositories import conversations as conv_repo
from nexo_api.repositories import messages as msg_repo
from nexo_api.repositories import run_events as event_repo
from nexo_api.repositories import runs as runs_repo
from nexo_api.repositories._base import load_json
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.conversation import MessageCreate
from nexo_api.schemas.run import (
    Identity,
    PublicRunEvent,
    RunAccepted,
    RunRequest,
    RunResult,
    RunStatus,
)
from nexo_api.services.orchestration.port import Orchestrator
from nexo_contracts import EventActor, EventType, EventVisibility, RunEvent


def _decode(prefix: str, wire_id: str, label: str) -> int:
    try:
        return ids.decode(prefix, wire_id)
    except ValueError as exc:
        raise ProblemException(
            status=404, code="RESOURCE_NOT_FOUND", title=f"{label} no encontrado", detail=str(exc)
        ) from exc


class RunOutcome:
    """Resultado interno de ejecutar un run (para reusar entre web y canales)."""

    def __init__(
        self, run_id_wire: str, status: RunStatus, answer: str, created_at: datetime
    ) -> None:
        self.run_id_wire = run_id_wire
        self.status = status
        self.answer = answer
        self.created_at = created_at


async def execute_run(
    tenant_id: int,
    conversation_id: int,
    user_message: str,
    channel: str,
    identity: Identity,
    trace_id: str,
    orchestrator: Orchestrator,
) -> RunOutcome:
    """Crea el run, invoca la orquestación y persiste eventos + snapshot.
    No guarda mensajes (eso lo hace el caller según el canal)."""
    run_row = await runs_repo.create(tenant_id, conversation_id, trace_id)
    run_id = int(run_row["id"])
    run_id_wire = ids.encode(ids.RUN, run_id)

    request = RunRequest(
        run_id=run_id_wire,
        trace_id=trace_id,
        conversation_id=ids.encode(ids.CONVERSATION, conversation_id),
        user_message=user_message,
        channel=channel,
        identity=identity,
    )
    result = await orchestrator.run(request)

    await event_repo.bulk_create(run_id, trace_id, result.events)
    metadata = {
        "answer": result.answer,
        "sources": result.sources,
        "available_actions": result.available_actions,
        "warnings": result.warnings,
        "metrics": result.metrics,
    }
    await runs_repo.finalize(
        tenant_id=tenant_id,
        run_id=run_id,
        status=result.status,
        domain=result.domain,
        metadata=metadata,
        latency_ms=int(result.metrics.get("latency_ms", 0)),
        total_cost_usd=float(result.metrics.get("total_cost_usd", 0.0)),
    )
    return RunOutcome(run_id_wire, result.status, result.answer, run_row["created_at"])


async def post_message(
    user: UserProfile,
    conversation_id_wire: str,
    body: MessageCreate,
    trace_id: str,
    orchestrator: Orchestrator,
) -> RunAccepted:
    tenant_id = int(user.tenant_id)
    conv_id = _decode(ids.CONVERSATION, conversation_id_wire, "conversación")

    conversation = await conv_repo.get(tenant_id, conv_id)
    if conversation is None:
        raise ProblemException(
            status=404, code="RESOURCE_NOT_FOUND", title="Conversación no encontrada"
        )

    await msg_repo.create(conv_id, "user", body.content)
    identity = Identity(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        roles=[user.role],
        permissions=user.permissions,
    )
    outcome = await execute_run(
        tenant_id,
        conv_id,
        body.content,
        str(conversation["channel"]),
        identity,
        trace_id,
        orchestrator,
    )
    await msg_repo.create(conv_id, "assistant", outcome.answer)

    return RunAccepted(
        run_id=outcome.run_id_wire,
        trace_id=trace_id,
        status=outcome.status,
        events_url=f"/api/v1/runs/{outcome.run_id_wire}/events",
        created_at=outcome.created_at,
    )


async def get_run(user: UserProfile, run_id_wire: str) -> RunResult:
    tenant_id = int(user.tenant_id)
    run_id = _decode(ids.RUN, run_id_wire, "run")
    row = await runs_repo.get(tenant_id, run_id)
    if row is None:
        raise ProblemException(status=404, code="RESOURCE_NOT_FOUND", title="Run no encontrado")

    meta = load_json(row["metadata"]) or {}
    return RunResult(
        run_id=run_id_wire,
        trace_id=row["trace_id"],
        status=row["status"],
        answer=meta.get("answer"),
        domain=row["domain"],
        sources=meta.get("sources", []),
        available_actions=meta.get("available_actions", []),
        warnings=meta.get("warnings", []),
        metrics=meta.get("metrics", {}),
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# SSE de eventos (Parte 3)
# ---------------------------------------------------------------------------
def public_run_event(event: RunEvent) -> PublicRunEvent:
    """Adapter explícito: nunca expone `RunEvent.data` en el SSE público."""
    restricted = event.visibility is EventVisibility.RESTRICTED
    return PublicRunEvent(
        event_id=event.event_id,
        run_id=event.run_id,
        trace_id=event.trace_id,
        sequence=event.sequence,
        type=event.type,
        status=event.status,
        actor_type=event.actor.type.value,
        actor_name="restringido" if restricted else event.actor.name,
        timestamp=event.timestamp,
        duration_ms=event.duration_ms,
        parent_event_id=event.parent_event_id,
        correlation_id=event.correlation_id,
        data=event.public_data,
    )


def _to_run_event(row: RowMapping, run_id_wire: str) -> RunEvent:
    canonical = load_json(_row(row, "canonical_event")) if "canonical_event" in row else None
    if canonical:
        event = RunEvent.model_validate(canonical)
        return event.model_copy(update={"run_id": run_id_wire})

    payload = load_json(row["payload"]) or {}
    public_data = load_json(_row(row, "public_data")) if "public_data" in row else None
    return RunEvent(
        event_id=str(_row(row, "event_id", f"evt_{row['id']}") or f"evt_{row['id']}"),
        run_id=run_id_wire,
        trace_id=row["trace_id"],
        sequence=int(_row(row, "sequence", row["id"]) or row["id"]),
        type=_event_type(str(row["event_type"])),
        timestamp=row["created_at"],
        actor=EventActor(
            type=_row(row, "actor_type", "system") or "system",
            name=_row(row, "actor_name", row["node_name"]) or row["node_name"],
        ),
        status=_row(row, "status", "succeeded") or "succeeded",
        visibility=_row(row, "visibility", "public") or "public",
        correlation_id=_row(row, "correlation_id", row["trace_id"]) or row["trace_id"],
        parent_event_id=_row(row, "parent_event_id"),
        duration_ms=_row(row, "duration_ms"),
        data=payload,
        public_data=public_data or payload,
        error=load_json(_row(row, "error")) if _row(row, "error") else None,
        policy_version=_row(row, "policy_version"),
        catalog_version=_row(row, "catalog_version"),
        skill_id=_row(row, "skill_id"),
        skill_version=_row(row, "skill_version"),
    )


def _row(row: RowMapping, key: str, default: object | None = None) -> object | None:
    return row[key] if key in row else default


def _event_type(value: str) -> EventType:
    legacy = {
        "node_start": EventType.AGENT_STARTED,
        "node_end": EventType.AGENT_COMPLETED,
        "rag_retrieval": EventType.RAG_COMPLETED,
        "mcp_call": EventType.TOOL_COMPLETED,
        "error": EventType.AGENT_FAILED,
    }
    if value in legacy:
        return legacy[value]
    return EventType(value)


async def get_run_for_stream(user: UserProfile, run_id_wire: str) -> tuple[int, str]:
    """Valida existencia/tenant antes de abrir el stream (para poder responder 404)."""
    tenant_id = int(user.tenant_id)
    run_id = _decode(ids.RUN, run_id_wire, "run")
    row = await runs_repo.get(tenant_id, run_id)
    if row is None:
        raise ProblemException(status=404, code="RESOURCE_NOT_FOUND", title="Run no encontrado")
    return run_id, str(row["status"])


async def event_stream(
    run_id_internal: int, run_id_wire: str, status: str, last_sequence: int
) -> AsyncGenerator[dict[str, str], None]:
    """Genera frames SSE con eventos posteriores a `last_sequence` (reanudable)."""
    rows = await event_repo.list_after(run_id_internal, last_sequence)
    for row in rows:
        event = _to_run_event(row, run_id_wire)
        public = public_run_event(event)
        yield {
            "id": str(event.sequence),
            "event": event.type.value,
            "data": public.model_dump_json(),
        }
    # Evento terminal con el estado final del run.
    yield {
        "event": "run.status",
        "data": json.dumps({"run_id": run_id_wire, "status": status}),
    }
