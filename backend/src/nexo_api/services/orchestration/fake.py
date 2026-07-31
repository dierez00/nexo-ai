"""Orquestador fake con el mismo contrato que el core canónico."""

from __future__ import annotations

from datetime import UTC, datetime

from nexo_api.services.orchestration.port import PendingActionSink
from nexo_contracts import (
    ActorType,
    EventActor,
    EventStatus,
    EventType,
    RunEvent,
    RunMetrics,
    RunRequest,
    RunResult,
    RunStatus,
)
from nexo_orchestration.ports import EventSinkPort


class FakeOrchestrator:
    async def run(
        self,
        request: RunRequest,
        event_sink: EventSinkPort,
        pending_actions: PendingActionSink,
        *,
        tenant_id: int,
    ) -> RunResult:
        del pending_actions, tenant_id
        for sequence, event_type, status in (
            (1, EventType.RUN_STARTED, EventStatus.STARTED),
            (2, EventType.RUN_COMPLETED, EventStatus.SUCCEEDED),
        ):
            await event_sink.emit(
                RunEvent(
                    event_id=f"evt_{str(request.run_id).removeprefix('run_')}_{sequence}",
                    trace_id=request.trace_id,
                    run_id=request.run_id,
                    sequence=sequence,
                    type=event_type,
                    timestamp=datetime.now(UTC),
                    actor=EventActor(type=ActorType.SUPERVISOR, name="fake_orchestrator"),
                    status=status,
                    correlation_id=request.trace_id,
                    data={"channel": request.channel.value},
                )
            )
        return RunResult(
            run_id=request.run_id,
            trace_id=request.trace_id,
            status=RunStatus.SUCCEEDED,
            answer=f"(demo) Recibí tu mensaje: «{request.user_message}».",
            warnings=["fake_orchestrator"],
            metrics=RunMetrics(duration_ms=0),
        )
