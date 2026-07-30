"""Smoke tests de los endpoints de salud."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


def test_live_ok(client: TestClient) -> None:
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}
    # trace_id se propaga en toda respuesta
    assert resp.headers["X-Trace-Id"].startswith("trace_")


def test_ready_ok_when_db_reachable(client: TestClient) -> None:
    async def _ok() -> bool:
        return True

    with patch("nexo_api.health.check_database", _ok):
        resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_ready_503_when_db_down(client: TestClient) -> None:
    async def _fail() -> bool:
        raise RuntimeError("db down")

    with patch("nexo_api.health.check_database", _fail):
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["checks"]["database"] == "error"
