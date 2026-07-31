"""Modelo falso programable por escenario (`DIE-F0-022`, `DIE-F0-023`).

El doble responde según la clave `purpose` de la solicitud, no según el texto del
prompt. Hacer matching sobre el prompt completo produce pruebas que se rompen al
reescribir una frase, lo que a su vez empuja a no mejorar los prompts.

Cada `purpose` puede programarse con un guion de varios turnos, de modo que la
primera invocación falle y la segunda tenga éxito. Es lo que permite probar
escalamiento, reintentos y fallback sin proveedor real.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from nexo_contracts import (
    ErrorCode,
    ModelDecision,
    ModelDecisionReason,
    NexoModel,
    NormalizedError,
    Outcome,
)

from ..models.adapters import AdapterResult
from ..ports.model import ChatRequest, ChatResponse, ModelPortError


class FakeBehavior(StrEnum):
    """Comportamientos que el modelo falso debe poder reproducir."""

    SUCCESS = "success"
    INVALID_OUTPUT = "invalid_output"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PROVIDER_DOWN = "provider_down"


_ERROR_BY_BEHAVIOR: dict[FakeBehavior, tuple[ErrorCode, str, Outcome]] = {
    FakeBehavior.INVALID_OUTPUT: (
        ErrorCode.MODEL_OUTPUT_INVALID,
        "La salida del modelo no cumple el contrato solicitado.",
        Outcome.KNOWN_FAILURE,
    ),
    FakeBehavior.TIMEOUT: (
        ErrorCode.RUN_TIMEOUT,
        "El modelo no respondió dentro del deadline.",
        Outcome.UNKNOWN,
    ),
    FakeBehavior.RATE_LIMIT: (
        ErrorCode.RATE_LIMITED,
        "El proveedor aplicó límite de tasa.",
        Outcome.KNOWN_FAILURE,
    ),
    FakeBehavior.PROVIDER_DOWN: (
        ErrorCode.MODEL_UNAVAILABLE,
        "El proveedor no está disponible.",
        Outcome.KNOWN_FAILURE,
    ),
}


@dataclass(frozen=True)
class Scenario:
    """Una respuesta programada para un `purpose`."""

    behavior: FakeBehavior = FakeBehavior.SUCCESS
    data: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 5
    input_tokens: int = 120
    output_tokens: int = 40
    cost_usd: float = 0.0
    retry_after_ms: int | None = None

    def error(self) -> NormalizedError:
        code, message, outcome = _ERROR_BY_BEHAVIOR[self.behavior]
        return NormalizedError.from_code(
            code,
            message,
            outcome=outcome,
            retry_after_ms=self.retry_after_ms,
        )


class ScenarioScript:
    """Guion de escenarios por `purpose`, con cursor propio.

    Se extrae del modelo falso para que el adapter falso del gateway comparta
    exactamente la misma mecánica: dos dobles que se comportan distinto ante el
    mismo guion harían inútil probar contra uno de ellos.
    """

    def __init__(
        self,
        scenarios: dict[str, Scenario | Sequence[Scenario]] | None = None,
        *,
        default: Scenario | None = None,
    ) -> None:
        self._scripts: dict[str, list[Scenario]] = {}
        for purpose, scenario in (scenarios or {}).items():
            self._scripts[purpose] = (
                [scenario] if isinstance(scenario, Scenario) else list(scenario)
            )
        self._default = default
        self._cursor: dict[str, int] = {}

    def program(self, purpose: str, *scenarios: Scenario) -> None:
        """Programa (o reprograma) el guion de un `purpose`."""
        self._scripts[purpose] = list(scenarios)
        self._cursor.pop(purpose, None)

    def next(self, purpose: str) -> Scenario:
        script = self._scripts.get(purpose)
        if not script:
            if self._default is not None:
                return self._default
            raise KeyError(
                f"el modelo falso no tiene escenario para el purpose {purpose!r}. "
                f"Programados: {sorted(self._scripts)}"
            )
        index = self._cursor.get(purpose, 0)
        # El último escenario se repite: un guion no tiene por qué anticipar
        # cuántos reintentos hará el router.
        scenario = script[min(index, len(script) - 1)]
        self._cursor[purpose] = index + 1
        return scenario


class FakeChatModel:
    """Implementación de `ChatModelPort` sin red, determinista y programable."""

    def __init__(
        self,
        scenarios: dict[str, Scenario | Sequence[Scenario]] | None = None,
        *,
        default: Scenario | None = None,
    ) -> None:
        self._script = ScenarioScript(scenarios, default=default)
        self.calls: list[ChatRequest] = []

    def program(self, purpose: str, *scenarios: Scenario) -> None:
        """Programa (o reprograma) el guion de un `purpose`."""
        self._script.program(purpose, *scenarios)

    def _next(self, purpose: str) -> Scenario:
        return self._script.next(purpose)

    async def generate(self, request: ChatRequest) -> ChatResponse:
        self.calls.append(request)
        scenario = self._next(request.purpose)

        if scenario.behavior is not FakeBehavior.SUCCESS:
            raise ModelPortError(scenario.error())

        return ChatResponse(
            data=scenario.data,
            decision=ModelDecision(
                requested_alias=request.alias,
                selected_alias=request.alias,
                reason=ModelDecisionReason.OFFLINE_PROFILE,
                policy_version="fake",
                max_cost_usd=request.max_cost_usd,
            ),
            input_tokens=scenario.input_tokens,
            output_tokens=scenario.output_tokens,
            estimated_cost_usd=scenario.cost_usd,
            duration_ms=scenario.latency_ms,
        )

    def call_count(self, purpose: str | None = None) -> int:
        if purpose is None:
            return len(self.calls)
        return sum(1 for call in self.calls if call.purpose == purpose)


class FakeChatAdapter:
    """Implementación de `ChatAdapterPort` para probar el gateway (`DIE-F1-007`).

    A diferencia de `FakeChatModel`, que sustituye al gateway entero, este doble
    sustituye solo al proveedor: el gateway real resuelve el alias, calcula el
    costo y decide el fallback por encima de él. Es lo que permite probar el
    routing sin credenciales y sin inventar un segundo mecanismo de escenarios.

    El costo lo calcula el gateway desde la configuración, así que
    `Scenario.cost_usd` se ignora aquí a propósito.
    """

    def __init__(
        self,
        scenarios: dict[str, Scenario | Sequence[Scenario]] | None = None,
        *,
        provider: str = "fake",
        default: Scenario | None = None,
    ) -> None:
        self._script = ScenarioScript(scenarios, default=default)
        self._provider = provider
        self.calls: list[tuple[str, str]] = []

    @property
    def provider(self) -> str:
        return self._provider

    def program(self, purpose: str, *scenarios: Scenario) -> None:
        self._script.program(purpose, *scenarios)

    async def generate(
        self,
        request: ChatRequest,
        *,
        model: str,
        output_contract: type[NexoModel] | None,
        max_output_tokens: int,
        timeout_ms: int,
    ) -> AdapterResult:
        del output_contract, max_output_tokens, timeout_ms
        self.calls.append((request.purpose, model))
        scenario = self._script.next(request.purpose)
        if scenario.behavior is not FakeBehavior.SUCCESS:
            raise ModelPortError(scenario.error())
        return AdapterResult(
            data=scenario.data,
            input_tokens=scenario.input_tokens,
            output_tokens=scenario.output_tokens,
            duration_ms=scenario.latency_ms,
        )

    def call_count(self, purpose: str | None = None) -> int:
        if purpose is None:
            return len(self.calls)
        return sum(1 for called, _ in self.calls if called == purpose)


class FakeEmbeddingsAdapter:
    """Implementación de `EmbeddingsAdapterPort` sobre embeddings deterministas.

    Existe para probar la resolución de alias del `EmbeddingsGateway`, no para
    medir calidad: los vectores no tienen propiedades semánticas (ver TD-02).
    """

    def __init__(self, *, provider: str = "fake", dimension: int = 64) -> None:
        self._provider = provider
        self._dimension = dimension
        self.calls: list[tuple[int, str]] = []

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str], *, model: str) -> list[list[float]]:
        self.calls.append((len(texts), model))
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [digest[index % len(digest)] / 255.0 for index in range(self._dimension)]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        return [value / norm for value in raw]
