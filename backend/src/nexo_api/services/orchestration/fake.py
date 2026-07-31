"""Orquestador fake para fase MVP (fixtures, §16).

Produce un `RunResult` canned y unos eventos, sin LLM ni RAG, para que el flujo
de chat funcione end-to-end. Se reemplaza por el orquestador real de Diego sin
tocar el backend (mismo `Orchestrator` Protocol).
"""

from __future__ import annotations

from datetime import UTC, datetime

from nexo_api.schemas.run import RunRequest
from nexo_api.services.orchestration.port import OrchestrationResult
from nexo_contracts import (
    ActorType,
    EventActor,
    EventStatus,
    EventType,
    EventVisibility,
    RunEvent,
)


class FakeOrchestrator:
    async def run(self, request: RunRequest) -> OrchestrationResult:
        events = [
            _event(
                request,
                1,
                EventType.AGENT_STARTED,
                EventStatus.STARTED,
                "classifier",
            ),
            _event(
                request,
                2,
                EventType.AGENT_COMPLETED,
                EventStatus.SUCCEEDED,
                "classifier",
                data={"domain": "general", "confidence": 0.5},
            ),
            _event(
                request,
                3,
                EventType.AGENT_COMPLETED,
                EventStatus.SUCCEEDED,
                "redactor",
                data={"channel": request.channel},
            ),
        ]
        return OrchestrationResult(
            status="completed",
            answer=(
                f"(demo) Recibí tu mensaje: «{request.user_message}». "
                "El orquestador real aún no está conectado."
            ),
            domain="general",
            warnings=["fake_orchestrator"],
            metrics={"latency_ms": 5, "total_cost_usd": 0.0},
            events=events,
        )


def _event(
    request: RunRequest,
    sequence: int,
    event_type: EventType,
    status: EventStatus,
    node: str,
    *,
    data: dict[str, object] | None = None,
) -> RunEvent:
    payload = {"node": node, **(data or {})}
    return RunEvent(
        event_id=f"evt_fake_{sequence:06d}",
        trace_id=request.trace_id,
        run_id=request.run_id,
        sequence=sequence,
        type=event_type,
        timestamp=datetime.now(UTC),
        actor=EventActor(type=ActorType.SUPERVISOR, name=node),
        status=status,
        visibility=EventVisibility.PUBLIC,
        correlation_id=request.trace_id,
        parent_event_id=f"evt_fake_{sequence - 1:06d}" if sequence > 1 else None,
        data=payload,
        public_data=payload,
    )
