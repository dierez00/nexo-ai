"""Tests de confirmación de acciones (idempotencia, consentimiento, RBAC)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.api.deps import get_current_user
from nexo_api.main import create_app
from nexo_api.schemas.auth import UserProfile

ADMIN = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="admin@demo.mx",
    name="Admin",
    role="admin",
    permissions=["vehiculos.write"],
)

ACTION = "vehiculos.reservar_cita"
KEY = "idem-key-123"

_ROW = {
    "id": 5,
    "idempotency_key": KEY,
    "action_name": ACTION,
    "status": "completed",
    "result_folio": "FOLIO-ABCD1234",
    "result_payload": {"echo": {}},
    "created_at": datetime.now(UTC),
}


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


def test_confirm_ok(client: TestClient) -> None:
    with (
        patch(
            "nexo_api.services.actions.service.actions_repo.find_by_idempotency_key",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "nexo_api.services.actions.service.actions_repo.create",
            new=AsyncMock(return_value=_ROW),
        ),
    ):
        resp = client.post(
            f"/api/v1/actions/{ACTION}/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "input": {"slot": "10:00"}},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action_id"] == "act_5"
    assert body["folio"] == "FOLIO-ABCD1234"


def test_replay_returns_same_without_second_write(client: TestClient) -> None:
    create_mock = AsyncMock()
    with (
        patch(
            "nexo_api.services.actions.service.actions_repo.find_by_idempotency_key",
            new=AsyncMock(return_value=_ROW),
        ),
        patch("nexo_api.services.actions.service.actions_repo.create", new=create_mock),
    ):
        resp = client.post(
            f"/api/v1/actions/{ACTION}/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True, "input": {"slot": "10:00"}},
        )
    assert resp.status_code == 200
    assert resp.json()["action_id"] == "act_5"
    create_mock.assert_not_called()  # replay: no segunda escritura


def test_missing_idempotency_key_400(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/actions/{ACTION}/confirm",
        json={"consent": True},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_missing_consent_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/actions/{ACTION}/confirm",
        headers={"Idempotency-Key": KEY},
        json={"consent": False},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "ACTION_CONFIRMATION_REQUIRED"


def test_permission_denied_403() -> None:
    no_perm = ADMIN.model_copy(update={"permissions": []})
    c = _client(no_perm)
    with c:
        resp = c.post(
            f"/api/v1/actions/{ACTION}/confirm",
            headers={"Idempotency-Key": KEY},
            json={"consent": True},
        )
    c.app.dependency_overrides.clear()  # type: ignore[attr-defined]
    assert resp.status_code == 403
    assert resp.json()["code"] == "PERMISSION_DENIED"
