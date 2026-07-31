"""Confirmación de acciones canónicas, sin dobles de esquema local."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.api.deps import get_action_executor, get_current_user
from nexo_api.main import create_app
from nexo_api.schemas.auth import UserProfile

from nexo_contracts import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ToolCallStatus,
    ToolConfirmation,
    ToolResult,
)

ADMIN = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="admin@demo.mx",
    name="Admin",
    role="admin",
    permissions=["vehiculos.write"],
)
KEY = "idem-key-123"
REQUEST = ActionRequest(
    action_id="act_5",
    run_id="run_42",
    tool_name="vehiculos.reservar_cita",
    input_schema_ref="contracts://vehiculos/reservar_cita.v1",
    tool_version="1.0.0",
    expected_version=1,
    parameters={"slot": "10:00"},
    required_permission="vehiculos.write",
)
ROW = {"request": REQUEST.model_dump(mode="json"), "status": "pending_confirmation"}
RESULT = ActionResult(
    action_id="act_5",
    status=ActionStatus.SUCCEEDED,
    tool_call_id="tc_5",
    tool_result=ToolResult(
        tool_call_id="tc_5",
        name="vehiculos.reservar_cita",
        status=ToolCallStatus.SUCCEEDED,
        confirmation=ToolConfirmation(identifier="FOLIO-5", issued_at="2026-01-01T00:00:00Z"),
        duration_ms=0,
    ),
)


def _client(user: UserProfile) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def client() -> Iterator[TestClient]:
    c = _client(ADMIN)
    with c:
        yield c
    c.app.dependency_overrides.clear()  # type: ignore[attr-defined]


OWNER = {"trace_id": "trace_42", "owner_user_id": 1}


def test_confirm_returns_canonical_action_result(client: TestClient) -> None:
    with (
        patch(
            "nexo_api.services.actions.service.pending_actions.get", new=AsyncMock(return_value=ROW)
        ),
        patch(
            "nexo_api.services.actions.service.pending_actions.owner_context",
            new=AsyncMock(return_value=OWNER),
        ),
        patch(
            "nexo_api.services.actions.service.idempotency.claim",
            new=AsyncMock(return_value=({"id": 1}, True)),
        ),
        patch("nexo_api.services.actions.service.pending_actions.complete", new=AsyncMock()),
        patch("nexo_api.services.actions.service.runs_repo.set_status", new=AsyncMock()),
        patch("nexo_api.services.actions.service.idempotency_repo.complete", new=AsyncMock()),
    ):
        response = client.post(
            "/api/v1/actions/act_5/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "expected_version": 1},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["tool_result"]["confirmation"]["identifier"].startswith("FOLIO-")


def test_replay_returns_canonical_result_without_executor(client: TestClient) -> None:
    replay = RESULT.model_dump(mode="json")
    with (
        patch(
            "nexo_api.services.actions.service.pending_actions.get", new=AsyncMock(return_value=ROW)
        ),
        patch(
            "nexo_api.services.actions.service.pending_actions.owner_context",
            new=AsyncMock(return_value=OWNER),
        ),
        patch(
            "nexo_api.services.actions.service.idempotency.claim",
            new=AsyncMock(return_value=({"id": 1, "response_body": replay}, False)),
        ),
    ):
        response = client.post(
            "/api/v1/actions/act_5/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "expected_version": 1},
        )
    assert response.status_code == 200
    assert response.json()["idempotency_replayed"] is True


def test_confirm_denied_when_action_belongs_to_another_user(client: TestClient) -> None:
    with (
        patch(
            "nexo_api.services.actions.service.pending_actions.get", new=AsyncMock(return_value=ROW)
        ),
        patch(
            "nexo_api.services.actions.service.pending_actions.owner_context",
            new=AsyncMock(return_value={"trace_id": "trace_42", "owner_user_id": 999}),
        ),
    ):
        response = client.post(
            "/api/v1/actions/act_5/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "expected_version": 1},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


def test_confirm_indeterminate_outcome_returns_503(client: TestClient) -> None:
    class _Boom:
        async def execute(self, action: ActionRequest, **_: object) -> ActionResult:
            raise RuntimeError("proveedor no respondió")

    with (
        patch(
            "nexo_api.services.actions.service.pending_actions.get", new=AsyncMock(return_value=ROW)
        ),
        patch(
            "nexo_api.services.actions.service.pending_actions.owner_context",
            new=AsyncMock(return_value=OWNER),
        ),
        patch(
            "nexo_api.services.actions.service.idempotency.claim",
            new=AsyncMock(return_value=({"id": 1}, True)),
        ),
        patch("nexo_api.services.actions.service.idempotency_repo.complete", new=AsyncMock()),
    ):
        client.app.dependency_overrides[get_action_executor] = lambda: _Boom()  # type: ignore[attr-defined]
        response = client.post(
            "/api/v1/actions/act_5/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "expected_version": 1},
        )
        client.app.dependency_overrides.pop(get_action_executor, None)  # type: ignore[attr-defined]
    assert response.status_code == 503
    assert response.json()["code"] == "UNKNOWN_OUTCOME"


def test_confirm_rejects_client_parameters(client: TestClient) -> None:
    response = client.post(
        "/api/v1/actions/act_5/confirm",
        headers={"Idempotency-Key": KEY},
        json={"consent": True, "expected_version": 1, "input": {"other": "value"}},
    )
    assert response.status_code == 422


def test_missing_consent_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/actions/act_5/confirm",
        headers={"Idempotency-Key": KEY},
        json={"consent": False, "expected_version": 1},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "ACTION_CONFIRMATION_REQUIRED"


def test_permission_denied_403() -> None:
    c = _client(ADMIN.model_copy(update={"permissions": []}))
    with (
        c,
        patch(
            "nexo_api.services.actions.service.pending_actions.get", new=AsyncMock(return_value=ROW)
        ),
    ):
        response = c.post(
            "/api/v1/actions/act_5/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "expected_version": 1},
        )
    c.app.dependency_overrides.clear()  # type: ignore[attr-defined]
    assert response.status_code == 403
