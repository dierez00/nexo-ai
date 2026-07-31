"""SSE usa los ``RunEvent`` y la secuencia canónicos."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.api.deps import get_current_user_sse
from nexo_api.main import create_app
from nexo_api.schemas.auth import UserProfile

from nexo_contracts import ActorType, EventActor, EventStatus, EventType, RunEvent

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


def _event(sequence: int) -> RunEvent:
    return RunEvent(
        event_id=f"evt_42_{sequence}",
        run_id="run_42",
        trace_id="trace_abc",
        sequence=sequence,
        type=EventType.RUN_COMPLETED,
        timestamp=datetime.now(UTC),
        actor=EventActor(type=ActorType.SUPERVISOR, name="test"),
        status=EventStatus.SUCCEEDED,
        correlation_id="trace_abc",
        data={"sequence": sequence},
    )


def test_sse_streams_canonical_events_and_terminal_status(client: TestClient) -> None:
    with (
        patch(
            "nexo_api.services.runs.service.runs_repo.get",
            new=AsyncMock(return_value={"status": "succeeded"}),
        ),
        patch(
            "nexo_api.services.runs.service.PostgresEventSink.read",
            new=AsyncMock(return_value=(_event(1), _event(2))),
        ),
        patch(
            "nexo_api.services.runs.service.runs_repo.get_status",
            new=AsyncMock(return_value="succeeded"),
        ),
    ):
        response = client.get("/api/v1/runs/run_42/events")
    assert response.status_code == 200
    assert "evt_42_1" in response.text
    assert "id: 2" in response.text
    assert "run.status" in response.text


def test_sse_resumes_after_last_event_id(client: TestClient) -> None:
    captured: dict[str, int] = {}

    async def read(_self: object, _run_id: str, *, after: int = 0) -> tuple[RunEvent, ...]:
        captured["after"] = after
        return (_event(2),)

    with (
        patch(
            "nexo_api.services.runs.service.runs_repo.get",
            new=AsyncMock(return_value={"status": "succeeded"}),
        ),
        patch("nexo_api.services.runs.service.PostgresEventSink.read", new=read),
        patch(
            "nexo_api.services.runs.service.runs_repo.get_status",
            new=AsyncMock(return_value="succeeded"),
        ),
    ):
        response = client.get("/api/v1/runs/run_42/events", headers={"Last-Event-ID": "1"})
    assert response.status_code == 200
    assert captured["after"] == 1


def test_sse_404_on_unknown_run(client: TestClient) -> None:
    with patch("nexo_api.services.runs.service.runs_repo.get", new=AsyncMock(return_value=None)):
        response = client.get("/api/v1/runs/run_999/events")
    assert response.status_code == 404
