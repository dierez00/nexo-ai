"""Runs HTTP adaptados a los contratos de ejecución compartidos."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import RowMapping

from nexo_api.core import ids
from nexo_api.core.errors import ProblemException
from nexo_api.repositories import conversations as conv_repo
from nexo_api.repositories import messages as msg_repo
from nexo_api.repositories import runs as runs_repo
from nexo_api.repositories._base import load_json
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.conversation import MessageCreate
from nexo_api.schemas.run import RunAccepted
from nexo_api.services.actions.pending_sink import PostgresPendingActionSink
from nexo_api.services.orchestration.port import Orchestrator
from nexo_api.services.runs.event_sink import PostgresEventSink
from nexo_api.services.runs.tasks import RunTaskManager
from nexo_contracts import (
    TERMINAL_RUN_STATUSES,
    ActorType,
    Channel,
    ErrorCode,
    EventActor,
    EventStatus,
    EventType,
    Identity,
    NormalizedError,
    RunEvent,
    RunRequest,
    RunResult,
    RunStatus,
)


def _decode(prefix: str, wire_id: str, label: str) -> int:
    try:
        return ids.decode(prefix, wire_id)
    except ValueError as exc:
        raise ProblemException(
            code="RESOURCE_NOT_FOUND", title=f"{label} no encontrado", detail=str(exc)
        ) from exc


def _identity(user: UserProfile) -> Identity:
    return Identity(
        user_id=ids.encode(ids.USER, int(user.user_id)),
        institution_id=ids.encode(ids.INSTITUTION, int(user.tenant_id)),
        roles=[user.role],
        permissions=user.permissions,
    )


def _channel(value: str) -> Channel:
    try:
        return Channel(value)
    except ValueError as exc:
        raise ProblemException(code="VALIDATION_ERROR", title="Canal no compatible") from exc


async def execute_run(
    tenant_id: int,
    conversation_id: int,
    user_message: str,
    channel: str,
    identity: Identity,
    trace_id: str,
    orchestrator: Orchestrator,
    run_row: RowMapping,
) -> RunResult:
    run_id = int(run_row["id"])
    run_id_wire = ids.encode(ids.RUN, run_id)
    await runs_repo.set_status(tenant_id, run_id, RunStatus.RUNNING.value)
    request = RunRequest(
        run_id=run_id_wire,
        trace_id=trace_id,
        conversation_id=ids.encode(ids.CONVERSATION, conversation_id),
        user_message=user_message,
        channel=_channel(channel),
        identity=identity,
        received_at=datetime.now(UTC),
    )
    result = await orchestrator.run(
        request,
        PostgresEventSink(),
        PostgresPendingActionSink(),
        tenant_id=tenant_id,
    )
    await runs_repo.finalize(
        tenant_id=tenant_id,
        run_id=run_id,
        status=result.status.value,
        domain=None,
        metadata=result.model_dump(mode="json"),
        latency_ms=result.metrics.duration_ms,
        total_cost_usd=result.metrics.total_cost_usd,
    )
    return result


async def post_message(
    user: UserProfile,
    conversation_id_wire: str,
    body: MessageCreate,
    trace_id: str,
    orchestrator: Orchestrator,
    task_manager: RunTaskManager,
) -> RunAccepted:
    tenant_id = int(user.tenant_id)
    conv_id = _decode(ids.CONVERSATION, conversation_id_wire, "conversación")
    conversation = await conv_repo.get(tenant_id, conv_id)
    if conversation is None:
        raise ProblemException(code="RESOURCE_NOT_FOUND", title="Conversación no encontrada")

    await msg_repo.create(conv_id, "user", body.content)
    run_row = await runs_repo.create(tenant_id, conv_id, trace_id, status=RunStatus.QUEUED.value)
    run_id = int(run_row["id"])
    run_id_wire = ids.encode(ids.RUN, run_id)

    async def _background() -> None:
        try:
            result = await execute_run(
                tenant_id,
                conv_id,
                body.content,
                str(conversation["channel"]),
                _identity(user),
                trace_id,
                orchestrator,
                run_row,
            )
            if result.answer:
                await msg_repo.create(conv_id, "assistant", result.answer)
        except Exception as exc:  # noqa: BLE001 - el fallo debe ser observable por SSE
            sink = PostgresEventSink()
            sequence = await sink.last_sequence(run_id_wire) + 1
            error = NormalizedError.from_code(ErrorCode.PROVIDER_ERROR, "Falló el orquestador")
            await sink.emit(
                RunEvent(
                    event_id=f"evt_{run_id}_{sequence}",
                    trace_id=trace_id,
                    run_id=run_id_wire,
                    sequence=sequence,
                    type=EventType.RUN_FAILED,
                    timestamp=datetime.now(UTC),
                    actor=EventActor(type=ActorType.SYSTEM, name="backend"),
                    status=EventStatus.FAILED,
                    data={"reason": type(exc).__name__},
                    error=error,
                )
            )
            await runs_repo.finalize(
                tenant_id,
                run_id,
                RunStatus.FAILED.value,
                None,
                RunResult(
                    run_id=run_id_wire,
                    trace_id=trace_id,
                    status=RunStatus.FAILED,
                    error=error,
                ).model_dump(mode="json"),
                0,
                0.0,
            )

    task_manager.submit(_background())
    return RunAccepted(
        run_id=run_id_wire,
        trace_id=trace_id,
        status=RunStatus.QUEUED,
        events_url=f"/api/v1/runs/{run_id_wire}/events",
        created_at=run_row["created_at"],
    )


async def get_run(user: UserProfile, run_id_wire: str) -> RunResult:
    run_id = _decode(ids.RUN, run_id_wire, "Run")
    row = await runs_repo.get(int(user.tenant_id), run_id)
    if row is None:
        raise ProblemException(code="RESOURCE_NOT_FOUND", title="Run no encontrado")
    metadata = load_json(row["metadata"]) or {}
    if metadata:
        return RunResult.model_validate(metadata)
    return RunResult(run_id=run_id_wire, trace_id=row["trace_id"], status=RunStatus(row["status"]))


async def get_run_for_stream(user: UserProfile, run_id_wire: str) -> tuple[int, RunStatus]:
    run_id = _decode(ids.RUN, run_id_wire, "Run")
    row = await runs_repo.get(int(user.tenant_id), run_id)
    if row is None:
        raise ProblemException(code="RESOURCE_NOT_FOUND", title="Run no encontrado")
    return run_id, RunStatus(row["status"])


async def event_stream(
    run_id_internal: int, run_id_wire: str, status: RunStatus, last_event_id: int
) -> AsyncGenerator[dict[str, str], None]:
    from nexo_api.core.config import get_settings

    settings = get_settings()
    sink = PostgresEventSink()
    sequence = last_event_id
    elapsed = 0
    while True:
        for event in await sink.read(run_id_wire, after=sequence):
            sequence = event.sequence
            yield {"id": str(sequence), "event": event.type.value, "data": event.model_dump_json()}
        current = await runs_repo.get_status(run_id_internal)
        status = RunStatus(current) if current else status
        if status in TERMINAL_RUN_STATUSES:
            yield {
                "event": "run.status",
                "data": json.dumps({"run_id": run_id_wire, "status": status.value}),
            }
            return
        await asyncio.sleep(settings.sse_poll_interval_ms / 1000)
        elapsed += settings.sse_poll_interval_ms
        if elapsed >= settings.sse_keepalive_seconds * 1000:
            elapsed = 0
            yield {"comment": "keepalive"}
