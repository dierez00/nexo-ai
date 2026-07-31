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
from nexo_api.schemas.run import Identity, RunAccepted, RunEvent, RunRequest, RunResult, RunStatus
from nexo_api.services.orchestration.port import Orchestrator


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

    await event_repo.bulk_create(
        run_id, trace_id, [(e.type, e.node_name, e.data) for e in result.events]
    )
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
def _to_run_event(row: RowMapping, run_id_wire: str) -> RunEvent:
    return RunEvent(
        event_id=f"evt_{row['id']}",
        run_id=run_id_wire,
        trace_id=row["trace_id"],
        sequence=int(row["id"]),
        type=row["event_type"],
        node_name=row["node_name"],
        timestamp=row["created_at"],
        data=load_json(row["payload"]) or {},
    )


async def get_run_for_stream(user: UserProfile, run_id_wire: str) -> tuple[int, str]:
    """Valida existencia/tenant antes de abrir el stream (para poder responder 404)."""
    tenant_id = int(user.tenant_id)
    run_id = _decode(ids.RUN, run_id_wire, "run")
    row = await runs_repo.get(tenant_id, run_id)
    if row is None:
        raise ProblemException(status=404, code="RESOURCE_NOT_FOUND", title="Run no encontrado")
    return run_id, str(row["status"])


async def event_stream(
    run_id_internal: int, run_id_wire: str, status: str, last_event_id: int
) -> AsyncGenerator[dict[str, str], None]:
    """Genera frames SSE con los eventos posteriores a `last_event_id` (reanudable)."""
    rows = await event_repo.list_after(run_id_internal, last_event_id)
    for row in rows:
        event = _to_run_event(row, run_id_wire)
        yield {"id": str(row["id"]), "event": event.type, "data": event.model_dump_json()}
    # Evento terminal con el estado final del run.
    yield {
        "event": "run.status",
        "data": json.dumps({"run_id": run_id_wire, "status": status}),
    }
