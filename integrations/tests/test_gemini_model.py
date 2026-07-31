"""Adapter Gemini sin red: wire shape, errores y cierre del cliente."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.genai import errors, types
from nexo_integrations.models import GeminiChatAdapter
from pydantic import Field

from nexo_contracts import ErrorCode, ModelTaskKind, NexoModel
from nexo_orchestration.ports.model import ChatRequest, ModelPortError

pytestmark = pytest.mark.unit


class Answer(NexoModel):
    answer: str = Field(max_length=100)


@dataclass
class _Models:
    response: object | None = None
    error: Exception | None = None

    def __post_init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    async def generate_content(self, **kwargs: Any) -> object:
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


class _Client:
    def __init__(self, models: _Models) -> None:
        self.models = models
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def _request() -> ChatRequest:
    return ChatRequest(
        purpose="write_answer",
        task_kind=ModelTaskKind.DRAFTING,
        alias="structured_small",
        output_contract="drafted_answer",
        prompt="Redacta únicamente los hechos verificados.",
        variables={},
        deadline_ms=6000,
    )


def _response(
    *,
    finish_reason: types.FinishReason = types.FinishReason.STOP,
    parsed: NexoModel | None = None,
) -> object:
    return SimpleNamespace(
        parsed=parsed,
        candidates=[SimpleNamespace(finish_reason=finish_reason)],
        usage_metadata=SimpleNamespace(
            prompt_token_count=123,
            candidates_token_count=17,
            thoughts_token_count=5,
        ),
    )


async def test_structured_request_and_usage_are_projected() -> None:
    models = _Models(response=_response(parsed=Answer(answer="Listo")))
    client = _Client(models)
    ticks = iter((100, 125))
    adapter = GeminiChatAdapter(
        api_key="test-key",
        client=client,  # type: ignore[arg-type]
        monotonic_ms=lambda: next(ticks),
    )

    result = await adapter.generate(
        _request(),
        model="gemini-3.6-flash",
        output_contract=Answer,
        max_output_tokens=4096,
        timeout_ms=2750,
    )

    assert result.data == {"answer": "Listo"}
    assert (result.input_tokens, result.output_tokens, result.duration_ms) == (123, 22, 25)
    assert models.kwargs["model"] == "gemini-3.6-flash"
    assert models.kwargs["contents"] == _request().prompt
    config = models.kwargs["config"]
    assert config.response_schema is Answer
    assert config.response_mime_type == "application/json"
    assert config.max_output_tokens == 4096
    assert config.http_options.timeout == 2750


def _api_error(status: int, **headers: str) -> errors.APIError:
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models")
    response = httpx.Response(status, request=request, headers=headers)
    error_type = errors.ServerError if status >= 500 else errors.ClientError
    return error_type(status, {"error": {"message": "provider failure"}}, response)


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (_api_error(429, **{"retry-after": "1.5"}), ErrorCode.RATE_LIMITED),
        (httpx.ReadTimeout("timed out"), ErrorCode.MODEL_UNAVAILABLE),
        (httpx.ConnectError("connection failed"), ErrorCode.MODEL_UNAVAILABLE),
        (_api_error(529), ErrorCode.PROVIDER_ERROR),
        (_api_error(401), ErrorCode.CONFIGURATION_INVALID),
        (_api_error(400), ErrorCode.CONFIGURATION_INVALID),
    ],
)
async def test_sdk_errors_are_normalized_without_provider_bodies(
    error: Exception, code: ErrorCode
) -> None:
    models = _Models(error=error)
    adapter = GeminiChatAdapter(
        api_key="test-key",
        client=_Client(models),  # type: ignore[arg-type]
        monotonic_ms=lambda: 10,
    )

    with pytest.raises(ModelPortError) as caught:
        await adapter.generate(
            _request(),
            model="gemini-3.6-flash",
            output_contract=Answer,
            max_output_tokens=100,
            timeout_ms=1000,
        )

    assert caught.value.error.code is code
    assert "provider failure" not in caught.value.error.message
    if code is ErrorCode.RATE_LIMITED:
        assert caught.value.error.retry_after_ms == 1500


@pytest.mark.parametrize(
    "finish_reason",
    [types.FinishReason.SAFETY, types.FinishReason.MAX_TOKENS],
)
async def test_incomplete_structured_outputs_preserve_billable_usage(
    finish_reason: types.FinishReason,
) -> None:
    adapter = GeminiChatAdapter(
        api_key="test-key",
        client=_Client(_Models(response=_response(finish_reason=finish_reason))),  # type: ignore[arg-type]
        monotonic_ms=lambda: 10,
    )

    with pytest.raises(ModelPortError) as caught:
        await adapter.generate(
            _request(),
            model="gemini-3.6-flash",
            output_contract=Answer,
            max_output_tokens=100,
            timeout_ms=1000,
        )

    assert caught.value.error.code is ErrorCode.MODEL_OUTPUT_INVALID
    assert (caught.value.input_tokens, caught.value.output_tokens) == (123, 22)


async def test_missing_parsed_output_is_invalid() -> None:
    adapter = GeminiChatAdapter(
        api_key="test-key",
        client=_Client(_Models(response=_response())),  # type: ignore[arg-type]
        monotonic_ms=lambda: 10,
    )

    with pytest.raises(ModelPortError) as caught:
        await adapter.generate(
            _request(),
            model="gemini-3.6-flash",
            output_contract=Answer,
            max_output_tokens=100,
            timeout_ms=1000,
        )

    assert caught.value.error.code is ErrorCode.MODEL_OUTPUT_INVALID


async def test_client_is_closed() -> None:
    client = _Client(_Models(response=_response(parsed=Answer(answer="ok"))))
    adapter = GeminiChatAdapter(
        api_key="test-key",
        client=client,  # type: ignore[arg-type]
    )

    await adapter.aclose()

    assert client.closed is True


def test_empty_api_key_is_rejected_without_an_injected_client() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiChatAdapter(api_key="  ")
