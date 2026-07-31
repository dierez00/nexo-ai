"""Tests del stream SSE de eventos de run (herméticos)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.api.deps import get_current_user_sse
from nexo_api.main import create_app
from nexo_api.schemas.auth import UserProfile

USER = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="demo@nexo.local",
    name="Demo",
    role="admin",
    permissions=[],
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_current_user_sse] = lambda: USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _event_row(event_id: int, event_type: str) -> dict[str, object]:
    return {
        "id": event_id,
        "trace_id": "trace_abc",
        "event_type": event_type,
        "node_name": "classifier",
        "payload": {"k": "v"},
        "created_at": datetime.now(UTC),
    }


def test_sse_streams_events_and_terminal_status(client: TestClient) -> None:
    rows = [_event_row(100, "node_start"), _event_row(101, "node_end")]
    with (
        patch(
            "nexo_api.services.runs.service.runs_repo.get",
            new=AsyncMock(return_value={"status": "completed"}),
        ),
        patch(
            "nexo_api.services.runs.service.event_repo.list_after",
            new=AsyncMock(return_value=rows),
        ),
    ):
        resp = client.get("/api/v1/runs/run_42/events")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "node_start" in body
    assert "evt_100" in body
    assert "id: 101" in body
    assert "run.status" in body  # evento terminal


def test_sse_resumes_after_last_event_id(client: TestClient) -> None:
    captured: dict[str, int] = {}

    async def _list_after(run_id: int, after_id: int = 0) -> list[dict[str, object]]:
        captured["after_id"] = after_id
        return [_event_row(102, "node_end")]

    with (
        patch(
            "nexo_api.services.runs.service.runs_repo.get",
            new=AsyncMock(return_value={"status": "completed"}),
        ),
        patch("nexo_api.services.runs.service.event_repo.list_after", new=_list_after),
    ):
        resp = client.get("/api/v1/runs/run_42/events", headers={"Last-Event-ID": "101"})
    assert resp.status_code == 200
    assert captured["after_id"] == 101  # reanuda desde el último recibido


def test_sse_404_on_unknown_run(client: TestClient) -> None:
    with patch(
        "nexo_api.services.runs.service.runs_repo.get",
        new=AsyncMock(return_value=None),
    ):
        resp = client.get("/api/v1/runs/run_999/events")
    assert resp.status_code == 404
