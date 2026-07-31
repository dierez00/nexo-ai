"""Tests del canal de voz síncrono (herméticos: repos y orquestador mockeados)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.api.deps import get_user_or_public
from nexo_api.main import create_app
from nexo_api.schemas.auth import UserProfile

from nexo_contracts import A2UIAction, RunResult, RunStatus

USER = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="demo@nexo.local",
    name="Demo",
    role="citizen",
    permissions=["domain:vehiculos:read"],
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_user_or_public] = lambda: USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _run_row() -> dict[str, Any]:
    return {"id": 50, "trace_id": "trace_v", "created_at": datetime.now(UTC)}


def test_voice_turn_creates_conversation_and_reads_answer(client: TestClient) -> None:
    """Sin conversation_id: crea una conversación de canal `voice` y devuelve la respuesta."""
    conv_row = {"id": 9, "channel": "voice", "status": "active", "title": None}
    result = RunResult(
        run_id="run_50",
        trace_id="trace_v",
        status=RunStatus.SUCCEEDED,
        answer="Necesitas tu identificación oficial.",
    )
    create_mock = AsyncMock(return_value=conv_row)
    with (
        patch("nexo_api.services.runs.service.conv_repo.create", new=create_mock),
        patch("nexo_api.services.runs.service.msg_repo.create", new=AsyncMock(return_value=1)),
        patch(
            "nexo_api.services.runs.service.runs_repo.create",
            new=AsyncMock(return_value=_run_row()),
        ),
        patch("nexo_api.services.runs.service.execute_run", new=AsyncMock(return_value=result)),
    ):
        resp = client.post(
            "/api/v1/voice/turn",
            json={"user_message": "qué necesito para mi licencia", "audience": "citizen"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_id"] == "conv_9"
    assert body["run_id"] == "run_50"
    assert body["status"] == "succeeded"
    assert body["answer"] == "Necesitas tu identificación oficial."
    assert body["pending_action"] is None
    # El canal creado es `voice`.
    assert create_mock.await_args is not None
    assert create_mock.await_args.kwargs["channel"] == "voice"


def test_voice_turn_surfaces_pending_action(client: TestClient) -> None:
    """Con acción de escritura: devuelve pending_action apto para confirmar por voz."""
    conv_row = {"id": 9, "channel": "voice", "status": "active", "title": None}
    result = RunResult(
        run_id="run_50",
        trace_id="trace_v",
        status=RunStatus.WAITING_CONFIRMATION,
        answer="Voy a reservar tu cita el martes. ¿Lo confirmo?",
        available_actions=[
            A2UIAction(
                action_id="act_7",
                tool_name="vehiculos.reservar_cita",
                input_schema_ref="contracts://vehiculos/reservar_cita",
                expected_version=1,
                requires_confirmation=True,
                label="Reservar cita",
            )
        ],
    )
    with (
        patch("nexo_api.services.runs.service.conv_repo.get", new=AsyncMock(return_value=conv_row)),
        patch("nexo_api.services.runs.service.msg_repo.create", new=AsyncMock(return_value=1)),
        patch(
            "nexo_api.services.runs.service.runs_repo.create",
            new=AsyncMock(return_value=_run_row()),
        ),
        patch("nexo_api.services.runs.service.execute_run", new=AsyncMock(return_value=result)),
    ):
        resp = client.post(
            "/api/v1/voice/turn",
            json={"conversation_id": "conv_9", "user_message": "quiero agendar mi cita"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "waiting_confirmation"
    assert body["pending_action"] == {
        "action_id": "act_7",
        "tool_name": "vehiculos.reservar_cita",
        "expected_version": 1,
        "label": "Reservar cita",
    }


def test_voice_turn_unknown_conversation_404(client: TestClient) -> None:
    with patch("nexo_api.services.runs.service.conv_repo.get", new=AsyncMock(return_value=None)):
        resp = client.post(
            "/api/v1/voice/turn",
            json={"conversation_id": "conv_404", "user_message": "hola"},
        )
    assert resp.status_code == 404
    assert resp.json()["code"] == "RESOURCE_NOT_FOUND"
