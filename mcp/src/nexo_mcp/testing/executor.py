"""Executor de tools en memoria (`DIE-F0-026`).

Reproduce los cinco desenlaces que el sistema debe saber manejar: éxito,
timeout, error de schema, permiso denegado y outcome desconocido. Este último es
el importante: es el único caso en el que no sabemos si la escritura ocurrió, y
por tanto el único que jamás puede reintentarse ni reportarse como éxito.

El executor **revalida** la autorización aunque el supervisor ya haya filtrado.
Confiar en que quien llama hizo su parte es exactamente lo que convierte un
guardrail en una sugerencia.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from nexo_contracts import (
    ErrorCode,
    NormalizedError,
    Outcome,
    ToolCall,
    ToolCallStatus,
    ToolConfirmation,
    ToolError,
    ToolMetadata,
    ToolMode,
    ToolResult,
)

from .registry import InMemoryToolRegistry


@runtime_checkable
class ClockLike(Protocol):
    """Fuente de tiempo mínima.

    Se declara aquí en vez de importarla de `orchestration` para no invertir la
    dependencia entre módulos. Al ser un `Protocol` estructural, el `FrozenClock`
    de la orquestación lo satisface sin que ninguno de los dos paquetes conozca
    al otro.
    """

    def now(self) -> datetime: ...


class _DefaultClock:
    """Reloj fijo de respaldo: los folios mock deben ser reproducibles."""

    def now(self) -> datetime:
        return datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


class ToolBehavior(StrEnum):
    """Desenlaces programables de una invocación."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    SCHEMA_ERROR = "schema_error"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN_OUTCOME = "unknown_outcome"
    NOT_FOUND = "not_found"


_ERROR_BY_BEHAVIOR: dict[ToolBehavior, tuple[ErrorCode, str, Outcome, ToolCallStatus]] = {
    ToolBehavior.TIMEOUT: (
        ErrorCode.TOOL_TIMEOUT,
        "La tool no respondió dentro del deadline.",
        Outcome.UNKNOWN,
        ToolCallStatus.TIMEOUT,
    ),
    ToolBehavior.SCHEMA_ERROR: (
        ErrorCode.VALIDATION_ERROR,
        "La salida de la tool no cumple su output schema.",
        Outcome.KNOWN_FAILURE,
        ToolCallStatus.FAILED,
    ),
    ToolBehavior.PERMISSION_DENIED: (
        ErrorCode.PERMISSION_DENIED,
        "El actor no está autorizado para esta operación.",
        Outcome.KNOWN_FAILURE,
        ToolCallStatus.DENIED,
    ),
    ToolBehavior.UNKNOWN_OUTCOME: (
        ErrorCode.UNKNOWN_OUTCOME,
        "La conexión se perdió tras enviar la operación; el efecto es desconocido.",
        Outcome.UNKNOWN,
        ToolCallStatus.FAILED,
    ),
    ToolBehavior.NOT_FOUND: (
        ErrorCode.RESOURCE_NOT_FOUND,
        "El recurso solicitado no existe o no es visible.",
        Outcome.KNOWN_FAILURE,
        ToolCallStatus.FAILED,
    ),
}


@dataclass(frozen=True)
class ToolScenario:
    """Respuesta programada de una tool."""

    behavior: ToolBehavior = ToolBehavior.SUCCESS
    data: dict[str, Any] = field(default_factory=dict)
    confirmation_identifier: str | None = None
    duration_ms: int = 20


class InMemoryToolExecutor:
    """Implementación de `ToolExecutorPort` sin red ni sistemas institucionales."""

    def __init__(
        self,
        registry: InMemoryToolRegistry,
        scenarios: dict[str, ToolScenario | Sequence[ToolScenario]] | None = None,
        *,
        clock: ClockLike | None = None,
    ) -> None:
        self._registry = registry
        self._clock = clock or _DefaultClock()
        self._scripts: dict[str, list[ToolScenario]] = {}
        for name, scenario in (scenarios or {}).items():
            self._scripts[name] = (
                [scenario] if isinstance(scenario, ToolScenario) else list(scenario)
            )
        self._cursor: dict[str, int] = {}
        self._idempotency: dict[str, ToolResult] = {}
        self.calls: list[ToolCall] = []

    def program(self, name: str, *scenarios: ToolScenario) -> None:
        self._scripts[name] = list(scenarios)
        self._cursor.pop(name, None)

    def _next(self, name: str) -> ToolScenario:
        script = self._scripts.get(name)
        if not script:
            return ToolScenario()
        index = self._cursor.get(name, 0)
        self._cursor[name] = index + 1
        return script[min(index, len(script) - 1)]

    def _authorize(self, call: ToolCall, metadata: ToolMetadata | None) -> str | None:
        """Motivo de denegación, o `None` si la invocación está autorizada."""
        if metadata is None:
            return "tool_not_registered"
        if not set(call.context.roles) & set(metadata.allowed_roles):
            return "role_not_allowed"
        if call.mode is not metadata.mode:
            return "mode_mismatch"
        if metadata.requires_confirmation and not call.confirmed:
            return "confirmation_required"
        if metadata.requires_idempotency_key and call.idempotency_key is None:
            return "idempotency_key_required"
        return None

    def _failure(
        self,
        call: ToolCall,
        behavior: ToolBehavior,
        duration_ms: int,
        *,
        detail: str | None = None,
    ) -> ToolResult:
        code, message, outcome, status = _ERROR_BY_BEHAVIOR[behavior]
        return ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=status,
            duration_ms=duration_ms,
            error=ToolError(
                error=NormalizedError.from_code(code, message, outcome=outcome),
                provider="mock",
                safe_details={"reason": detail} if detail else {},
            ),
        )

    async def execute(self, call: ToolCall) -> ToolResult:
        self.calls.append(call)
        metadata = await self._registry.get(call.name, call.version)

        denial = self._authorize(call, metadata)
        if denial is not None:
            behavior = (
                ToolBehavior.NOT_FOUND
                if denial == "tool_not_registered"
                else ToolBehavior.PERMISSION_DENIED
            )
            return self._failure(call, behavior, 0, detail=denial)

        # Idempotencia: repetir una confirmación devuelve el resultado original
        # marcado como replay, sin emitir una segunda escritura (`DIE-F1-080`).
        if call.idempotency_key is not None:
            replayed = self._idempotency.get(call.idempotency_key)
            if replayed is not None:
                return replayed.model_copy(update={"idempotency_replayed": True})

        scenario = self._next(call.name)
        if scenario.behavior is not ToolBehavior.SUCCESS:
            return self._failure(call, scenario.behavior, scenario.duration_ms)

        confirmation = None
        if call.mode is ToolMode.WRITE:
            identifier = scenario.confirmation_identifier or f"NEXO-MOCK-{call.tool_call_id}"
            confirmation = ToolConfirmation(
                identifier=identifier,
                identifier_kind="folio",
                is_mock=True,
                issued_at=self._clock.now(),
            )

        result = ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=ToolCallStatus.SUCCEEDED,
            data=scenario.data,
            confirmation=confirmation,
            provider="mock",
            duration_ms=scenario.duration_ms,
            is_mock=True,
        )
        if call.idempotency_key is not None:
            self._idempotency[call.idempotency_key] = result
        return result
