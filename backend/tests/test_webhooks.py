"""Tests de webhooks Twilio: firma real, dedupe y status 204 (herméticos)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from nexo_api.core.config import get_settings
from nexo_api.main import create_app
from twilio.request_validator import RequestValidator

from nexo_contracts import RunMetrics, RunResult, RunStatus

# La URL debe coincidir con la que el server usa para validar la firma
# (PUBLIC_BASE_URL + path), sin importar qué valor tenga hoy el .env.
_BASE = get_settings().public_base_url.rstrip("/")
WEBHOOK_URL = f"{_BASE}/webhooks/twilio/whatsapp"
STATUS_URL = f"{_BASE}/webhooks/twilio/status"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


def _sign(url: str, params: dict[str, str]) -> str:
    token = get_settings().twilio_auth_token.get_secret_value()
    return str(RequestValidator(token).compute_signature(url, params))


def test_whatsapp_valid_signature_triggers_run(client: TestClient) -> None:
    params = {
        "MessageSid": "SM123",
        "From": "whatsapp:+5215500000000",
        "To": "whatsapp:+14155238886",
        "Body": "hola",
    }
    conv = {
        "id": 9,
        "channel": "whatsapp",
        "status": "active",
        "title": None,
        "created_at": datetime.now(UTC),
    }
    with (
        patch(
            "nexo_api.services.channels.service.conv_repo.find_by_channel_ref",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "nexo_api.services.channels.service.conv_repo.create",
            new=AsyncMock(return_value=conv),
        ),
        patch(
            "nexo_api.services.channels.service.msg_repo.exists_provider_message",
            new=AsyncMock(return_value=False),
        ),
        patch("nexo_api.services.channels.service.msg_repo.create", new=AsyncMock(return_value=1)),
        patch(
            "nexo_api.services.channels.service.runs_repo.create",
            new=AsyncMock(
                return_value={"id": 3, "trace_id": "trace_test", "created_at": datetime.now(UTC)}
            ),
        ),
        patch(
            "nexo_api.services.channels.service.execute_run",
            new=AsyncMock(
                return_value=RunResult(
                    run_id="run_3",
                    trace_id="trace_test",
                    status=RunStatus.SUCCEEDED,
                    answer="respuesta",
                    metrics=RunMetrics(duration_ms=0),
                )
            ),
        ),
    ):
        resp = client.post(
            "/webhooks/twilio/whatsapp",
            data=params,
            headers={"X-Twilio-Signature": _sign(WEBHOOK_URL, params)},
        )
    assert resp.status_code == 200
    assert "<Message>" in resp.text  # TwiML con respuesta


def test_whatsapp_invalid_signature_403(client: TestClient) -> None:
    params = {"MessageSid": "SM1", "From": "whatsapp:+521", "To": "w", "Body": "x"}
    resp = client.post(
        "/webhooks/twilio/whatsapp",
        data=params,
        headers={"X-Twilio-Signature": "firma-invalida"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "PERMISSION_DENIED"


def test_whatsapp_duplicate_is_deduped(client: TestClient) -> None:
    params = {
        "MessageSid": "SM-dup",
        "From": "whatsapp:+5215500000000",
        "To": "whatsapp:+14155238886",
        "Body": "hola",
    }
    conv = {
        "id": 9,
        "channel": "whatsapp",
        "status": "active",
        "title": None,
        "created_at": datetime.now(UTC),
    }
    run_create = AsyncMock()
    with (
        patch(
            "nexo_api.services.channels.service.conv_repo.find_by_channel_ref",
            new=AsyncMock(return_value=conv),
        ),
        patch(
            "nexo_api.services.channels.service.msg_repo.exists_provider_message",
            new=AsyncMock(return_value=True),
        ),
        patch("nexo_api.services.channels.service.runs_repo.create", new=run_create),
    ):
        resp = client.post(
            "/webhooks/twilio/whatsapp",
            data=params,
            headers={"X-Twilio-Signature": _sign(WEBHOOK_URL, params)},
        )
    assert resp.status_code == 200
    assert "<Message>" not in resp.text  # ack vacío, sin respuesta
    run_create.assert_not_called()  # no se disparó run para el duplicado


def test_status_valid_signature_204(client: TestClient) -> None:
    params = {"MessageSid": "SM1", "MessageStatus": "delivered"}
    with patch(
        "nexo_api.services.channels.service.msg_repo.set_delivery_status",
        new=AsyncMock(return_value=None),
    ):
        resp = client.post(
            "/webhooks/twilio/status",
            data=params,
            headers={"X-Twilio-Signature": _sign(STATUS_URL, params)},
        )
    assert resp.status_code == 204
