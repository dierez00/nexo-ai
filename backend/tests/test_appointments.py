"""Tests de citas: disponibilidad, holds y conflicto GiST (herméticos)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.api.deps import get_current_user
from nexo_api.main import create_app
from nexo_api.schemas.auth import UserProfile
from sqlalchemy.exc import IntegrityError

ADMIN = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="admin@demo.mx",
    name="Admin",
    role="admin",
    permissions=["vehiculos.read", "vehiculos.write"],
)
KEY = "idem-hold-123"
_RECORD = {"id": 1, "request_hash": "hash", "status": "processing"}


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


def test_availability_marks_taken_slot(client: TestClient) -> None:
    taken = [
        {
            "starts_at": datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
            "ends_at": datetime(2026, 8, 1, 9, 30, tzinfo=UTC),
        }
    ]
    with patch(
        "nexo_api.services.appointments.service.appts_repo.list_active_in_range",
        new=AsyncMock(return_value=taken),
    ):
        resp = client.get(
            "/api/v1/appointments/availability",
            params={"branch_id": 1, "module_code": "vehiculos", "date": "2026-08-01"},
        )
    assert resp.status_code == 200
    slots = resp.json()
    assert slots[0]["available"] is False  # 09:00 ocupado
    assert slots[1]["available"] is True  # 09:30 libre


def test_create_hold_ok(client: TestClient) -> None:
    row = {
        "id": 3,
        "status": "hold",
        "hold_expires_at": datetime(2026, 8, 1, 10, 15, tzinfo=UTC),
        "starts_at": datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 8, 1, 10, 30, tzinfo=UTC),
    }
    with (
        patch(
            "nexo_api.services.appointments.service.branches_repo.exists",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "nexo_api.services.appointments.service.appts_repo.create_hold",
            new=AsyncMock(return_value=row),
        ),
        patch(
            "nexo_api.services.appointments.service.idempotency.claim",
            new=AsyncMock(return_value=(_RECORD, True)),
        ),
        patch("nexo_api.services.appointments.service.idempotency_repo.complete", new=AsyncMock()),
    ):
        resp = client.post(
            "/api/v1/appointments/holds",
            headers={"Idempotency-Key": KEY},
            json={
                "branch_id": 1,
                "module_code": "vehiculos",
                "service_name": "renovacion",
                "starts_at": "2026-08-01T10:00:00Z",
                "ends_at": "2026-08-01T10:30:00Z",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["appointment_id"] == "apt_3"
    assert resp.json()["status"] == "hold"


def test_create_hold_overlap_409(client: TestClient) -> None:
    err = IntegrityError("overlap", None, Exception("exclusion"))
    with (
        patch(
            "nexo_api.services.appointments.service.branches_repo.exists",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "nexo_api.services.appointments.service.appts_repo.create_hold",
            new=AsyncMock(side_effect=err),
        ),
        patch(
            "nexo_api.services.appointments.service.idempotency.claim",
            new=AsyncMock(return_value=(_RECORD, True)),
        ),
        patch("nexo_api.services.appointments.service.idempotency_repo.complete", new=AsyncMock()),
    ):
        resp = client.post(
            "/api/v1/appointments/holds",
            headers={"Idempotency-Key": KEY},
            json={
                "branch_id": 1,
                "module_code": "vehiculos",
                "service_name": "renovacion",
                "starts_at": "2026-08-01T10:00:00Z",
                "ends_at": "2026-08-01T10:30:00Z",
            },
        )
    assert resp.status_code == 409
    assert resp.json()["code"] == "APPOINTMENT_CONFLICT"


def test_create_hold_unknown_branch_404(client: TestClient) -> None:
    with patch(
        "nexo_api.services.appointments.service.branches_repo.exists",
        new=AsyncMock(return_value=False),
    ):
        resp = client.post(
            "/api/v1/appointments/holds",
            headers={"Idempotency-Key": KEY},
            json={
                "branch_id": 999,
                "module_code": "vehiculos",
                "service_name": "renovacion",
                "starts_at": "2026-08-01T10:00:00Z",
                "ends_at": "2026-08-01T10:30:00Z",
            },
        )
    assert resp.status_code == 404


def test_create_hold_requires_idempotency_key(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/appointments/holds",
        json={
            "branch_id": 1,
            "module_code": "vehiculos",
            "service_name": "renovacion",
            "starts_at": "2026-08-01T10:00:00Z",
            "ends_at": "2026-08-01T10:30:00Z",
        },
    )
    assert resp.status_code == 400


def test_availability_permission_denied_403() -> None:
    no_perm = ADMIN.model_copy(update={"permissions": []})
    c = _client(no_perm)
    with c:
        resp = c.get(
            "/api/v1/appointments/availability",
            params={"branch_id": 1, "module_code": "vehiculos", "date": "2026-08-01"},
        )
    c.app.dependency_overrides.clear()  # type: ignore[attr-defined]
    assert resp.status_code == 403
