"""Smoke del perfil `real`: el recorrido vehicular llega a confirmación.

Ensambla el grafo MVP real (tools mock, modelo falso) como lo hace la app en el
perfil `real` y corre el recorrido `CAP-VEH-01` sin base de datos: usa un event
sink y un sink de acciones en memoria. Valida que el orquestador real:

- llega a `waiting_confirmation` con estimación y fuentes, y
- persiste la `ActionRequest` para que el cliente pueda confirmarla.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from nexo_api.services.orchestration import RealOrchestrator, build_graph_deps

from nexo_contracts import ActionRequest, Channel, Identity, RunRequest, RunStatus
from nexo_orchestration.testing import InMemoryEventSink

pytestmark = pytest.mark.e2e


class _CapturingSink:
    def __init__(self) -> None:
        self.persisted: list[tuple[ActionRequest, int]] = []

    async def persist(self, action: ActionRequest, *, tenant_id: int) -> None:
        self.persisted.append((action, tenant_id))


def _request() -> RunRequest:
    return RunRequest(
        run_id="run_000001",
        trace_id="trace_000001",
        conversation_id="conv_000001",
        user_message="Quiero renovar mi licencia y saber si debo algo",
        channel=Channel.WEB,
        identity=Identity(
            user_id="usr_demo",
            institution_id="inst_demo",
            roles=["citizen"],
            permissions=[
                "domain:vehiculos:read",
                "domain:registro_civil:read",
                "domain:salud:read",
                "appointment:create",
            ],
        ),
        received_at=datetime.now(UTC),
    )


async def test_real_run_reaches_confirmation_and_persists_the_action() -> None:
    assembly = await build_graph_deps()
    orchestrator = RealOrchestrator(assembly)
    sink = _CapturingSink()

    result = await orchestrator.run(
        _request(), InMemoryEventSink(), sink, tenant_id=1
    )

    assert result.status is RunStatus.WAITING_CONFIRMATION
    assert result.estimate is not None
    assert result.sources
    assert result.available_actions and result.available_actions[0].requires_confirmation

    assert sink.persisted, "la acción pendiente debe persistirse para poder confirmarla"
    action, tenant_id = sink.persisted[0]
    assert tenant_id == 1
    assert action.tool_name == "vehiculos.reservar_cita"
