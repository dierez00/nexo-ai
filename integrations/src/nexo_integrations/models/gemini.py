"""Adapter de Gemini para el gateway de modelos de Nexo IA.

El SDK queda confinado en este módulo. Los agentes y el gateway solo observan
`ChatAdapterPort`, `AdapterResult` y errores normalizados; ningún prompt,
respuesta o detalle de credenciales cruza la frontera de errores.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from typing import Any, Protocol, cast

import httpx
from google import genai
from google.genai import errors, types
from pydantic import JsonValue, ValidationError

from nexo_contracts import ErrorCode, NexoModel, NormalizedError
from nexo_orchestration.models import AdapterResult
from nexo_orchestration.ports.model import ChatRequest, ModelPortError

# Subconjunto documentado por `GenerateContentConfig.response_json_schema`.
# Los límites que Gemini no entiende se conservan en el contrato Pydantic y se
# aplican al validar la respuesta, pero no deben provocar que el proveedor
# rechace la solicitud antes de inferir.
_SUPPORTED_JSON_SCHEMA_KEYS = frozenset(
    {
        "$id",
        "$defs",
        "$ref",
        "$anchor",
        "type",
        "format",
        "title",
        "description",
        "enum",
        "items",
        "prefixItems",
        "minimum",
        "maximum",
        "anyOf",
        "oneOf",
        "properties",
        "additionalProperties",
        "required",
        "propertyOrdering",
    }
)

# La Gemini Developer API rechaza deadlines de transporte menores a 10 s.
# Nexo conserva su deadline lógico por separado con ``asyncio.timeout`` para
# que elevar este valor no permita que una invocación exceda su presupuesto.
_MIN_PROVIDER_TIMEOUT_MS = 10_000


def _gemini_response_schema(output_contract: type[NexoModel]) -> dict[str, Any]:
    """Proyecta el JSON Schema de Pydantic al subconjunto aceptado por Gemini.

    `response_schema` usa el dialecto OpenAPI reducido del SDK y serializa
    `additionalProperties` como un campo que la Gemini Developer API rechaza.
    `response_json_schema` sí soporta esa palabra estándar, pero no todas las
    restricciones que Pydantic publica. En particular, límites altos de arrays
    (`maxItems=50/100`) hacen que Gemini rechace contratos anidados válidos por
    complejidad. La validación completa se repite sobre la respuesta en
    :meth:`generate`, por lo que retirarlas aquí no debilita el contrato interno.
    """

    def project(schema: JsonValue) -> JsonValue:
        if isinstance(schema, list):
            return [project(item) for item in schema]
        if not isinstance(schema, dict):
            return schema

        projected: dict[str, JsonValue] = {}
        for key, value in schema.items():
            if key not in _SUPPORTED_JSON_SCHEMA_KEYS:
                continue
            if key in {"properties", "$defs"}:
                if isinstance(value, dict):
                    projected[key] = {name: project(child) for name, child in value.items()}
            elif key == "additionalProperties" and isinstance(value, dict):
                projected[key] = project(value)
            else:
                projected[key] = project(value)

        # Pydantic representa `Literal` con `const`, que no está en el
        # subconjunto de Gemini. Un enum unitario expresa la misma restricción.
        if "const" in schema and "enum" not in projected:
            projected["enum"] = [schema["const"]]
        return projected

    return cast(dict[str, Any], project(output_contract.model_json_schema()))


class _Usage(Protocol):
    prompt_token_count: int | None
    candidates_token_count: int | None
    thoughts_token_count: int | None


class _Candidate(Protocol):
    finish_reason: types.FinishReason | str | None


class _Response(Protocol):
    parsed: Any
    usage_metadata: _Usage | None
    candidates: list[_Candidate] | None


class _Models(Protocol):
    async def generate_content(self, **kwargs: Any) -> _Response: ...


class _AsyncClient(Protocol):
    models: _Models

    async def aclose(self) -> None: ...


def _monotonic_ms() -> int:
    return time.monotonic_ns() // 1_000_000


def _retry_after_ms(exc: errors.APIError) -> int | None:
    """Lee `retry-after` sin conservar headers ni cuerpos del proveedor."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(0, int(float(raw) * 1000))
    except (TypeError, ValueError):
        return None


def _normalized_error(exc: Exception) -> NormalizedError:
    """Traduce excepciones tipadas del SDK a códigos estables de Nexo."""
    if isinstance(exc, errors.APIError):
        if exc.code == 429:
            return NormalizedError.from_code(
                ErrorCode.RATE_LIMITED,
                "Gemini alcanzó el límite temporal de solicitudes",
                retry_after_ms=_retry_after_ms(exc),
            )
        if exc.code == 408:
            return NormalizedError.from_code(
                ErrorCode.MODEL_UNAVAILABLE,
                "Gemini no estuvo disponible dentro del tiempo permitido",
            )
        if exc.code >= 500:
            return NormalizedError.from_code(
                ErrorCode.PROVIDER_ERROR,
                "Gemini devolvió un fallo temporal del proveedor",
            )
        return NormalizedError.from_code(
            ErrorCode.CONFIGURATION_INVALID,
            "la configuración de la API de Gemini fue rechazada",
        )
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, TimeoutError)):
        return NormalizedError.from_code(
            ErrorCode.MODEL_UNAVAILABLE,
            "Gemini no estuvo disponible dentro del tiempo permitido",
        )
    if isinstance(exc, (ValidationError, ValueError)):
        return NormalizedError.from_code(
            ErrorCode.CONFIGURATION_INVALID,
            "la configuración de la API de Gemini fue rechazada",
        )
    return NormalizedError.from_code(
        ErrorCode.PROVIDER_ERROR,
        "la invocación de Gemini falló de forma inesperada",
    )


def _usage(response: _Response) -> tuple[int, int]:
    usage = response.usage_metadata
    if usage is None:
        return 0, 0
    input_tokens = usage.prompt_token_count or 0
    # Gemini factura los tokens de razonamiento como salida.
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return input_tokens, output_tokens


def _finish_reason(response: _Response) -> str | None:
    if not response.candidates:
        return None
    raw = response.candidates[0].finish_reason
    return raw.value if isinstance(raw, types.FinishReason) else raw


def _json_text_payload(raw: str) -> Any:
    """Carga JSON de respuestas que el SDK no alcanzó a poblar en `parsed`."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _structured_payload(response: _Response) -> Any:
    parsed = response.parsed
    if isinstance(parsed, str):
        return _json_text_payload(parsed)
    if parsed is not None:
        return parsed

    try:
        text = getattr(response, "text")
    except Exception:
        text = None
    if isinstance(text, str) and text.strip():
        return _json_text_payload(text)
    raise ValueError("salida estructurada ausente")


class GeminiChatAdapter:
    """`ChatAdapterPort` asíncrono sobre Gemini generateContent."""

    def __init__(
        self,
        *,
        api_key: str,
        client: _AsyncClient | None = None,
        monotonic_ms: Callable[[], int] = _monotonic_ms,
    ) -> None:
        if not api_key.strip() and client is None:
            raise ValueError("GEMINI_API_KEY está vacía")
        if client is None:
            # `retry_options=None` es el modo sin reintentos del SDK. La única
            # política de retry vive en ModelGateway y queda auditada allí.
            sdk_client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(retry_options=None),
            )
            client = cast(_AsyncClient, sdk_client.aio)
        self._client = client
        self._monotonic_ms = monotonic_ms

    @property
    def provider(self) -> str:
        return "gemini"

    async def generate(
        self,
        request: ChatRequest,
        *,
        model: str,
        output_contract: type[NexoModel] | None,
        max_output_tokens: int,
        timeout_ms: int,
    ) -> AdapterResult:
        if output_contract is None:
            raise ModelPortError(
                NormalizedError.from_code(
                    ErrorCode.CONFIGURATION_INVALID,
                    "Gemini requiere un contrato de salida estructurada",
                )
            )

        started_ms = self._monotonic_ms()
        try:
            async with asyncio.timeout(max(0.001, timeout_ms / 1000)):
                response = await self._client.models.generate_content(
                    model=model,
                    contents=request.prompt,
                    config=types.GenerateContentConfig(
                        http_options=types.HttpOptions(
                            timeout=max(_MIN_PROVIDER_TIMEOUT_MS, timeout_ms)
                        ),
                        max_output_tokens=max_output_tokens,
                        response_mime_type="application/json",
                        response_json_schema=_gemini_response_schema(output_contract),
                    ),
                )
        except Exception as exc:
            duration_ms = max(0, self._monotonic_ms() - started_ms)
            raise ModelPortError(
                _normalized_error(exc),
                duration_ms=duration_ms,
            ) from exc

        duration_ms = max(0, self._monotonic_ms() - started_ms)
        input_tokens, output_tokens = _usage(response)
        finish_reason = _finish_reason(response)
        if finish_reason != types.FinishReason.STOP.value:
            raise ModelPortError(
                NormalizedError.from_code(
                    ErrorCode.MODEL_OUTPUT_INVALID,
                    "Gemini no completó el contrato de salida solicitado",
                ),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            )

        try:
            parsed = _structured_payload(response)
            validated = output_contract.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise ModelPortError(
                NormalizedError.from_code(
                    ErrorCode.MODEL_OUTPUT_INVALID,
                    "Gemini no produjo una salida estructurada válida",
                ),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            ) from exc

        data = cast(dict[str, JsonValue], validated.model_dump(mode="json"))
        return AdapterResult(
            data=data,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
        )

    async def aclose(self) -> None:
        """Libera el pool HTTP del SDK durante el shutdown de FastAPI."""
        await self._client.aclose()
