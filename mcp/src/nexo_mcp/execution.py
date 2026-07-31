"""Ejecución de tools: validar, autorizar, invocar y normalizar (F1.8).

El orden es el que importa y no es negociable:

    revalidar permiso → validar input → invocar adapter → validar output

**Revalidar** (`DIE-F2-013`) porque el executor no confía en que el supervisor
filtrara ni en que el agente respetara la lista. **Validar el input antes**
(`DIE-F1-067`) porque un adapter que recibe basura puede hacer cualquier cosa,
incluida una escritura parcial. **Validar el output después** porque un adapter
—o un sistema institucional— puede devolver algo que su propio contrato no
admite, y propagarlo convertiría un fallo de integración en un hecho falso.

Dos reglas sobre reintentos:

- solo se reintentan lecturas seguras (`DIE-F1-068`);
- una escritura con outcome desconocido **jamás** se reintenta. No es
  configurable: `UNKNOWN_OUTCOME` no puede aparecer en un `retry_on` porque el
  contrato de configuración lo rechaza, y aquí tampoco se consulta.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from pydantic import ValidationError

from nexo_contracts import (
    ErrorCode,
    NexoModel,
    NormalizedError,
    Outcome,
    ToolCall,
    ToolCallStatus,
    ToolConfirmation,
    ToolError,
    ToolMode,
    ToolResult,
)

from .authorization import AuthorizationDecision, DenialReason, PermissionMatrix
from .catalog import ToolCatalog
from .tools.definitions import ToolDefinition

# Códigos que admiten reintento en una lectura. Deliberadamente corto y
# deliberadamente sin `UNKNOWN_OUTCOME`.
RETRYABLE_READ_CODES = frozenset({ErrorCode.TOOL_TIMEOUT, ErrorCode.PROVIDER_ERROR})


@runtime_checkable
class ClockLike(Protocol):
    """Fuente de tiempo mínima; ver D-06 sobre por qué se declara aquí."""

    def now(self) -> datetime: ...


class _DefaultClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


class AdapterFailure(Exception):
    """Fallo simulado o real de un adapter, ya normalizado."""

    def __init__(self, code: ErrorCode, message: str, *, outcome: Outcome) -> None:
        self.error = NormalizedError.from_code(code, message, outcome=outcome)
        super().__init__(message)


@dataclass
class ToolExecutor:
    """Executor real de tools sobre el catálogo configurado."""

    catalog: ToolCatalog
    permissions: PermissionMatrix
    clock: ClockLike = field(default_factory=_DefaultClock)
    # Fallos inyectables por nombre de tool, para ejercer los desenlaces sin
    # inventar un segundo executor de pruebas.
    failures: dict[str, AdapterFailure] = field(default_factory=dict)
    _idempotency: dict[str, ToolResult] = field(default_factory=dict, init=False)
    calls: list[ToolCall] = field(default_factory=list, init=False)

    async def execute(self, call: ToolCall) -> ToolResult:
        """Ejecuta la invocación. Nunca lanza: los fallos viajan en el resultado."""
        self.calls.append(call)

        definition = self.catalog.definition(call.name, call.version)
        decision = self._authorize(call, definition)
        if not decision.allowed:
            assert decision.reason is not None
            return self._denied(call, decision.reason)

        assert definition is not None

        # Idempotencia (`DIE-F1-080`): repetir una confirmación devuelve el
        # resultado original marcado como replay, sin una segunda escritura.
        if call.idempotency_key is not None:
            replayed = self._idempotency.get(call.idempotency_key)
            if replayed is not None:
                return replayed.model_copy(update={"idempotency_replayed": True})

        result = await self._invoke_with_retries(call, definition)

        if call.idempotency_key is not None and result.status is ToolCallStatus.SUCCEEDED:
            self._idempotency[call.idempotency_key] = result
        return result

    # -- autorización -------------------------------------------------------

    def _authorize(
        self, call: ToolCall, definition: ToolDefinition | None
    ) -> AuthorizationDecision:
        if definition is None:
            return AuthorizationDecision.deny(DenialReason.TOOL_NOT_REGISTERED)

        metadata = definition.metadata
        if call.mode is not metadata.mode:
            # Pedir en modo lectura algo que escribe —o al revés— no es un
            # detalle: es un intento de saltarse las reglas del modo.
            return AuthorizationDecision.deny(DenialReason.MODE_NOT_GRANTED)
        if not set(call.context.roles) & set(metadata.allowed_roles):
            return AuthorizationDecision.deny(DenialReason.ROLE_NOT_ALLOWED)
        if metadata.requires_confirmation and not call.confirmed:
            return AuthorizationDecision.deny(DenialReason.CONFIRMATION_REQUIRED)
        if metadata.requires_idempotency_key and call.idempotency_key is None:
            return AuthorizationDecision.deny(DenialReason.IDEMPOTENCY_KEY_REQUIRED)

        return self.permissions.grants(
            institution_id=call.context.institution_id,
            roles=list(call.context.roles),
            tool=metadata,
            mode=call.mode,
        )

    # -- invocación ---------------------------------------------------------

    async def _invoke_with_retries(self, call: ToolCall, definition: ToolDefinition) -> ToolResult:
        metadata = definition.metadata
        # `DIE-F1-068`: una escritura tiene `max_attempts == 1` por contrato.
        attempts = 1 if metadata.mode is ToolMode.WRITE else metadata.max_attempts
        last: ToolResult | None = None

        for attempt in range(1, attempts + 1):
            last = await self._invoke_once(call, definition)
            if last.status is ToolCallStatus.SUCCEEDED:
                return last
            code = last.error.code if last.error else None
            retryable = (
                metadata.mode is not ToolMode.WRITE
                and code in RETRYABLE_READ_CODES
                and attempt < attempts
            )
            if not retryable:
                return last
        assert last is not None
        return last

    async def _invoke_once(self, call: ToolCall, definition: ToolDefinition) -> ToolResult:
        metadata = definition.metadata

        try:
            payload = definition.input_model.model_validate(call.parameters)
        except ValidationError as exc:
            return self._failed(
                call,
                ErrorCode.VALIDATION_ERROR,
                _first_error(exc, "la entrada no cumple el input schema de la tool"),
                outcome=Outcome.KNOWN_FAILURE,
            )

        failure = self.failures.get(call.name)
        if failure is not None:
            return self._failed(
                call,
                failure.error.code,
                failure.error.message,
                outcome=failure.error.outcome,
            )

        try:
            raw = await asyncio.wait_for(
                _run(definition, payload), timeout=metadata.timeout_ms / 1000
            )
        except TimeoutError:
            # El outcome de un timeout de escritura es **desconocido**: la
            # operación pudo aplicarse. Es lo que impide reintentarla.
            return self._failed(
                call,
                ErrorCode.TOOL_TIMEOUT,
                f"la tool no respondió en {metadata.timeout_ms} ms",
                outcome=(
                    Outcome.UNKNOWN if metadata.mode is ToolMode.WRITE else Outcome.KNOWN_FAILURE
                ),
            )

        try:
            validated = definition.output_model.model_validate(raw.model_dump(mode="json"))
        except ValidationError as exc:
            return self._failed(
                call,
                ErrorCode.VALIDATION_ERROR,
                _first_error(exc, "la salida del adapter no cumple su output schema"),
                outcome=Outcome.KNOWN_FAILURE,
            )

        confirmation = None
        if metadata.mode is ToolMode.WRITE:
            # `DIE-F1-078`: sin folio no hay éxito. El identificador se deriva
            # del `tool_call_id`, que es reproducible.
            confirmation = ToolConfirmation(
                identifier=f"NEXO-MOCK-{call.tool_call_id.removeprefix('tc_').upper()}",
                identifier_kind="folio",
                is_mock=metadata.is_mock,
                issued_at=self.clock.now(),
            )

        return ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=ToolCallStatus.SUCCEEDED,
            data=validated.model_dump(mode="json"),
            confirmation=confirmation,
            provider="mock" if metadata.is_mock else "adapter",
            duration_ms=1,
            is_mock=metadata.is_mock,
        )

    # -- resultados de fallo ------------------------------------------------

    def _denied(self, call: ToolCall, reason: DenialReason) -> ToolResult:
        code = (
            ErrorCode.TOOL_NOT_FOUND
            if reason is DenialReason.TOOL_NOT_REGISTERED
            else ErrorCode.PERMISSION_DENIED
        )
        return ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=(
                ToolCallStatus.FAILED
                if reason is DenialReason.TOOL_NOT_REGISTERED
                else ToolCallStatus.DENIED
            ),
            duration_ms=0,
            error=ToolError(
                error=NormalizedError.from_code(
                    code, "la invocación no está autorizada", outcome=Outcome.KNOWN_FAILURE
                ),
                provider="mcp",
                # El motivo viaja como código estable, no como explicación: qué
                # regla faltó es auditoría, no respuesta (`DIE-F2-015`).
                safe_details={"reason": reason.value},
            ),
        )

    def _failed(
        self, call: ToolCall, code: ErrorCode, message: str, *, outcome: Outcome
    ) -> ToolResult:
        status = ToolCallStatus.TIMEOUT if code is ErrorCode.TOOL_TIMEOUT else ToolCallStatus.FAILED
        return ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=status,
            duration_ms=0,
            error=ToolError(
                error=NormalizedError.from_code(code, message, outcome=outcome),
                provider="mock",
                safe_details={},
            ),
        )


async def _run(definition: ToolDefinition, payload: NexoModel) -> NexoModel:
    """Invoca el adapter. Está aparte para poder envolverlo en un timeout."""
    return definition.handler(payload)


def _first_error(exc: ValidationError, prefix: str) -> str:
    """Mensaje accionable sin transportar el valor recibido."""
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first["loc"]) or "<raíz>"
    return f"{prefix}: campo {location!r} — {first['msg']}"


def audit_payload(call: ToolCall, result: ToolResult) -> dict[str, str | int | bool]:
    """Datos de auditoría minimizados (`DIE-F1-070`, `DIE-F1-082`).

    Registra **la forma** de la invocación, nunca sus parámetros: un adeudo
    lleva la referencia del vehículo y un registro de solicitud el predio. Lo
    que hace falta para reconstruir el run es qué tool, con qué permiso, con qué
    desenlace, no con qué datos.
    """
    return {
        "tool": call.name,
        "version": call.version,
        "mode": call.mode.value,
        "confirmed": call.confirmed,
        "has_idempotency_key": call.idempotency_key is not None,
        "parameter_count": len(call.parameters),
        "status": result.status.value,
        "is_mock": result.is_mock,
        "idempotency_replayed": result.idempotency_replayed,
        "error_code": result.error.error.code.value if result.error else "",
        "outcome": result.error.error.outcome.value if result.error else "known_success",
    }


def has_unknown_outcome(result: ToolResult) -> bool:
    """Si el efecto de la operación es incierto (`DIE-F1-077`, `DIE-F1-081`)."""
    return result.error is not None and result.error.error.outcome is Outcome.UNKNOWN


def only_reads(results: Sequence[ToolResult]) -> bool:
    """Utilidad de auditoría: ninguna de estas invocaciones fue una escritura."""
    return all(result.confirmation is None for result in results)
