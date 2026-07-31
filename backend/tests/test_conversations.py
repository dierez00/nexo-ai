"""Tests de conversaciones/runs (herméticos: repos y auth mockeados)."""

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

USER = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="demo@nexo.local",
    name="Demo",
    role="admin",
    permissions=["citas.read"],
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_user_or_public] = lambda: USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_conversation(client: TestClient) -> None:
    row = {
        "id": 7,
        "channel": "web",
        "status": "active",
        "title": None,
        "created_at": datetime.now(UTC),
    }
    with patch(
        "nexo_api.services.conversations.service.conv_repo.create",
        new=AsyncMock(return_value=row),
    ):
        resp = client.post("/api/v1/conversations", json={"channel": "web"})
    assert resp.status_code == 201
    assert resp.json()["conversation_id"] == "conv_7"


def test_create_conversation_public_without_token() -> None:
    """Sin Authorization: se resuelve el ciudadano anónimo y user_id queda NULL."""
    app = create_app()
    row = {
        "id": 8,
        "channel": "web",
        "status": "active",
        "title": None,
        "created_at": datetime.now(UTC),
    }
    create_mock = AsyncMock(return_value=row)
    with (
        TestClient(app) as c,
        patch("nexo_api.api.deps.tenants_repo.id_by_slug", new=AsyncMock(return_value=1)),
        patch("nexo_api.services.conversations.service.conv_repo.create", new=create_mock),
    ):
        resp = c.post("/api/v1/conversations", json={"channel": "web"})
    assert resp.status_code == 201
    assert create_mock.await_args is not None
    assert create_mock.await_args.kwargs["user_id"] is None


def test_post_message_returns_202_run_accepted(client: TestClient) -> None:
    conv_row: dict[str, Any] = {"id": 7, "channel": "web", "status": "active", "title": None}
    run_row = {"id": 42, "trace_id": "trace_abc", "created_at": datetime.now(UTC)}

    with (
        patch(
            "nexo_api.services.runs.service.conv_repo.get",
            new=AsyncMock(return_value=conv_row),
        ),
        patch("nexo_api.services.runs.service.msg_repo.create", new=AsyncMock(return_value=1)),
        patch(
            "nexo_api.services.runs.service.runs_repo.create",
            new=AsyncMock(return_value=run_row),
        ),
        patch(
            "nexo_api.services.runs.tasks.RunTaskManager.submit",
            side_effect=lambda coroutine: coroutine.close(),
        ),
    ):
        resp = client.post("/api/v1/conversations/conv_7/messages", json={"content": "hola"})

    assert resp.status_code == 202
    body = resp.json()
    assert body["run_id"] == "run_42"
    assert body["status"] == "queued"
    assert body["events_url"] == "/api/v1/runs/run_42/events"


def test_get_run_snapshot(client: TestClient) -> None:
    row = {
        "trace_id": "trace_abc",
        "status": "succeeded",
        "metadata": {
            "run_id": "run_42",
            "trace_id": "trace_abc",
            "status": "succeeded",
            "answer": "hola",
            "metrics": {"duration_ms": 0},
        },
        "created_at": datetime.now(UTC),
    }
    with patch(
        "nexo_api.services.runs.service.runs_repo.get",
        new=AsyncMock(return_value=row),
    ):
        resp = client.get("/api/v1/runs/run_42")
    assert resp.status_code == 200
    assert resp.json()["answer"] == "hola"


def test_get_run_bad_id_404(client: TestClient) -> None:
    resp = client.get("/api/v1/runs/notanid")
    assert resp.status_code == 404
    assert resp.json()["code"] == "RESOURCE_NOT_FOUND"
