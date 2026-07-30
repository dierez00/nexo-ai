"""Tests de auth (herméticos): validación JWKS, perfil y login proxy mockeados."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.auth.schemas import UserProfile
from nexo_api.main import create_app

PROFILE = UserProfile(
    user_id="1",
    auth_user_id="00000000-0000-0000-0000-000000000001",
    tenant_id="1",
    email="demo@nexo.local",
    name="Demo",
    role="admin",
    permissions=["citas.read", "citas.write"],
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


# ---- /users/me (validación de token) ---------------------------------------
def test_users_me_requires_token(client: TestClient) -> None:
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_users_me_ok_with_valid_token(client: TestClient) -> None:
    with (
        patch("nexo_api.auth.dependencies.verify_supabase_jwt", return_value={"sub": "abc"}),
        patch(
            "nexo_api.auth.dependencies.load_profile_by_auth_id",
            new=AsyncMock(return_value=PROFILE),
        ),
    ):
        resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer faketoken"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "demo@nexo.local"
    assert resp.headers["X-Trace-Id"].startswith("trace_")


def test_users_me_403_when_not_provisioned(client: TestClient) -> None:
    with (
        patch("nexo_api.auth.dependencies.verify_supabase_jwt", return_value={"sub": "abc"}),
        patch(
            "nexo_api.auth.dependencies.load_profile_by_auth_id",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer faketoken"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "PERMISSION_DENIED"


def test_users_me_401_on_invalid_token(client: TestClient) -> None:
    import jwt

    with patch(
        "nexo_api.auth.dependencies.verify_supabase_jwt",
        side_effect=jwt.InvalidTokenError("bad"),
    ):
        resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401


# ---- /auth/login (proxy a Supabase Auth) -----------------------------------
def _fake_client(session: object | None, user: object | None) -> object:
    sign_in = AsyncMock(return_value=type("R", (), {"session": session, "user": user})())
    auth = type("Auth", (), {"sign_in_with_password": sign_in})()
    return type("Client", (), {"auth": auth})()


def test_login_ok(client: TestClient) -> None:
    session = type("S", (), {"access_token": "acc.jwt.tok", "refresh_token": "ref"})()
    user = type("U", (), {"id": "abc"})()
    fake = _fake_client(session, user)

    async def _create(url: str, key: str) -> Any:
        return fake

    with (
        patch("nexo_api.auth.service.create_supabase_client", new=_create),
        patch(
            "nexo_api.auth.service.load_profile_by_auth_id",
            new=AsyncMock(return_value=PROFILE),
        ),
    ):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "demo@nexo.local", "password": "x"},
        )
    assert resp.status_code == 200
    assert resp.json()["tokens"]["access_token"] == "acc.jwt.tok"


def test_login_bad_credentials_401(client: TestClient) -> None:
    fake = _fake_client(None, None)

    async def _create(url: str, key: str) -> Any:
        return fake

    with patch("nexo_api.auth.service.create_supabase_client", new=_create):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "demo@nexo.local", "password": "wrong"},
        )
    assert resp.status_code == 401
    assert resp.json()["code"] == "AUTHENTICATION_REQUIRED"
