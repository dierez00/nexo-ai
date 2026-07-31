"""Orquestador fake para fase MVP (fixtures, §16).

Produce un `RunResult` canned y unos eventos, sin LLM ni RAG, para que el flujo
de chat funcione end-to-end. Se reemplaza por el orquestador real de Diego sin
tocar el backend (mismo `Orchestrator` Protocol).
"""

from __future__ import annotations

from nexo_api.schemas.run import RunRequest
from nexo_api.services.orchestration.port import EmittedEvent, OrchestrationResult


class FakeOrchestrator:
    async def run(self, request: RunRequest) -> OrchestrationResult:
        events = [
            EmittedEvent(
                type="node_start",
                node_name="classifier",
                data={"user_message": request.user_message},
            ),
            EmittedEvent(
                type="node_end",
                node_name="classifier",
                data={"domain": "general", "confidence": 0.5},
            ),
            EmittedEvent(
                type="node_end",
                node_name="redactor",
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
