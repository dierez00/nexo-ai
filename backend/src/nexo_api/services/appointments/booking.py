"""Persistencia de la cita que produce una acción confirmada.

La tool de escritura del MCP es un mock: valida el esquema, exige confirmación e
idempotency key y emite un folio, pero no deja rastro. Sin este módulo, «tu cita
quedó agendada con folio X» sería una frase sin nada detrás — no aparecería en
seguimiento, no bloquearía el horario y no sobreviviría a un reinicio.

Aquí se traduce el resultado de la tool a una fila real de `public.appointments`.
El conflicto de horario lo decide el constraint GiST, que es la única autoridad
capaz de resolver dos confirmaciones simultáneas por el mismo hueco.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError

from nexo_api.repositories import appointments as appts_repo
from nexo_api.repositories import branches as branches_repo
from nexo_contracts import ActionRequest, ToolResult

# Duración del slot agendado desde el chat, alineada con `/appointments`.
_SLOT_MINUTES = 30

# Tools de escritura que agendan atención presencial, con el módulo y el nombre
# de servicio con los que se registra la cita.
_BOOKING_TOOLS: dict[str, tuple[str, str]] = {
    "vehiculos.reservar_cita": ("vehiculos", "Renovación de licencia de conducir"),
    "ayuntamiento.registrar_solicitud": ("ayuntamiento_empresas", "Apertura de establecimiento"),
}

# Campo del que cada tool publica el inicio de la cita en su salida.
_START_FIELDS = ("inicio", "cita_inicio")


@dataclass(frozen=True)
class BookingOutcome:
    """Resultado de intentar persistir la cita de una acción confirmada."""

    appointment_id: int | None = None
    starts_at: datetime | None = None
    conflict: bool = False
    skipped_reason: str | None = None

    @property
    def booked(self) -> bool:
        return self.appointment_id is not None


def _start_from(result: ToolResult) -> datetime | None:
    for field in _START_FIELDS:
        raw = result.data.get(field)
        if isinstance(raw, str):
            try:
                parsed = datetime.fromisoformat(raw)
            except ValueError:
                continue
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
        if isinstance(raw, datetime):
            return raw if raw.tzinfo is not None else raw.replace(tzinfo=UTC)
    return None


async def book_confirmed_action(
    action: ActionRequest,
    result: ToolResult,
    *,
    tenant_id: int,
    user_id: int | None,
    trace_id: str,
) -> BookingOutcome:
    """Persiste la cita de una acción confirmada, si la tool agenda una.

    No lanza: una acción que no agenda (o que no trae horario) no es un error,
    solo no produce cita. El único fallo propagable es el conflicto de horario,
    que el llamador convierte en un `ActionResult` fallido.
    """
    booking = _BOOKING_TOOLS.get(action.tool_name)
    if booking is None:
        return BookingOutcome(skipped_reason="tool_does_not_book")

    module_code, service_name = booking
    starts_at = _start_from(result)
    if starts_at is None:
        return BookingOutcome(skipped_reason="no_start_time")

    folio = result.confirmation.identifier if result.confirmation else None
    if folio is None:
        return BookingOutcome(skipped_reason="no_folio")

    branch_id = await branches_repo.default_id(tenant_id)
    if branch_id is None:
        return BookingOutcome(skipped_reason="no_branch")

    metadata: dict[str, Any] = {
        "run_id": action.run_id,
        "action_id": action.action_id,
        "trace_id": trace_id,
        "tool_call_id": result.tool_call_id,
        "tool_name": action.tool_name,
        "is_mock": result.is_mock,
    }

    try:
        row = await appts_repo.create_confirmed(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user_id,
            module_code=module_code,
            service_name=service_name,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(minutes=_SLOT_MINUTES),
            folio=folio,
            metadata=metadata,
        )
    except IntegrityError:
        return BookingOutcome(conflict=True, starts_at=starts_at)

    return BookingOutcome(appointment_id=int(row["id"]), starts_at=row["starts_at"])
