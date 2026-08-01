"""Tests de superficies A2UI admin (herméticos: auth y repos mockeados)."""

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
    email="admin@nexo.local",
    name="Admin",
    role="admin",
    permissions=["admin.read"],
)

CITIZEN = ADMIN.model_copy(update={"role": "citizen"})


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _metrics() -> dict[str, object]:
    return {
        "runs": {
            "total": 8,
            "avg_latency_ms": 812.4,
            "total_cost_usd": 0.1234,
            "by_status": {"succeeded": 6, "failed": 2},
            "by_domain": {"vehiculos": 5, "salud": 3},
        },
        "conversations_total": 3,
        "actions": {"total": 2, "by_status": {"confirmed": 2}},
        "appointments": {"total": 1, "by_status": {"held": 1}},
    }


def test_admin_chart_surface_requires_token() -> None:
    with TestClient(create_app()) as client:
        resp = client.post("/api/v1/admin/a2ui/charts", json={"prompt": "trámites por dominio"})

    assert resp.status_code == 401


def test_admin_chart_surface_requires_admin_role() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: CITIZEN
    with TestClient(app) as client:
        resp = client.post("/api/v1/admin/a2ui/charts", json={"prompt": "trámites por dominio"})
    app.dependency_overrides.clear()

    assert resp.status_code == 403


def test_admin_chart_surface_returns_valid_a2ui(client: TestClient) -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 31, tzinfo=UTC)
    collect = AsyncMock(return_value=_metrics())
    trend = AsyncMock(
        return_value=[{"date": "2026-07-30", "total": 8, "succeeded": 6}]
    )

    with (
        patch("nexo_api.services.admin.metrics.metrics_repo.collect", new=collect),
        patch("nexo_api.services.admin.metrics.metrics_repo.collect_runs_trend", new=trend),
    ):
        resp = client.post(
            "/api/v1/admin/a2ui/charts",
            json={
                "prompt": "trámites por dominio en 30 días",
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["catalog_id"] == "urn:nexo-ia:a2ui:catalog:admin:v1"
    assert body["actions"] == []
    assert collect.await_args is not None
    assert collect.await_args.args[0] == 1
    assert collect.await_args.args[1] == start
    assert collect.await_args.args[2] == end


def test_admin_chart_surface_unsupported_prompt_still_returns_surface(
    client: TestClient,
) -> None:
    collect = AsyncMock(return_value=_metrics())
    trend = AsyncMock(return_value=[])
    with (
        patch("nexo_api.services.admin.metrics.metrics_repo.collect", new=collect),
        patch("nexo_api.services.admin.metrics.metrics_repo.collect_runs_trend", new=trend),
    ):
        resp = client.post("/api/v1/admin/a2ui/charts", json={"prompt": "haz magia"})

    assert resp.status_code == 200
    assert resp.json()["catalog_id"] == "urn:nexo-ia:a2ui:catalog:admin:v1"
