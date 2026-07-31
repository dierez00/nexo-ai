"""Casos de uso de citas: disponibilidad y creación de holds."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from nexo_api.core import ids
from nexo_api.core.errors import ProblemException
from nexo_api.repositories import appointments as appts_repo
from nexo_api.repositories import branches as branches_repo
from nexo_api.repositories import idempotency as idempotency_repo
from nexo_api.schemas.appointment import AppointmentHold, AppointmentSlot, HoldCreate
from nexo_api.schemas.auth import UserProfile
from nexo_api.services import idempotency

# Horario de atención (UTC) y tamaño de slot para el MVP.
_DAY_START_HOUR = 9
_DAY_END_HOUR = 17
_SLOT_MINUTES = 30


def _ensure_permission(user: UserProfile, permission: str) -> None:
    if permission not in user.permissions:
        raise ProblemException(
            status=403,
            code="PERMISSION_DENIED",
            title="Permiso insuficiente",
            detail=f"Se requiere el permiso '{permission}'.",
        )


def _to_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def get_availability(
    user: UserProfile, branch_id: int, module_code: str, day: date
) -> list[AppointmentSlot]:
    _ensure_permission(user, f"{module_code}.read")
    tenant_id = int(user.tenant_id)

    start = datetime(day.year, day.month, day.day, _DAY_START_HOUR, tzinfo=UTC)
    end = datetime(day.year, day.month, day.day, _DAY_END_HOUR, tzinfo=UTC)
    taken = [
        (row["starts_at"], row["ends_at"])
        for row in await appts_repo.list_active_in_range(tenant_id, branch_id, start, end)
    ]

    slots: list[AppointmentSlot] = []
    cursor = start
    step = timedelta(minutes=_SLOT_MINUTES)
    while cursor < end:
        slot_end = cursor + step
        available = not any(s < slot_end and cursor < e for s, e in taken)
        slots.append(AppointmentSlot(starts_at=cursor, ends_at=slot_end, available=available))
        cursor = slot_end
    return slots


async def create_hold(
    user: UserProfile, body: HoldCreate, idempotency_key: str | None
) -> AppointmentHold:
    _ensure_permission(user, f"{body.module_code}.write")
    tenant_id = int(user.tenant_id)

    if not idempotency_key:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            title="Falta el header Idempotency-Key",
            detail="Toda escritura requiere el header 'Idempotency-Key'.",
        )

    if not await branches_repo.exists(tenant_id, body.branch_id):
        raise ProblemException(
            status=404, code="RESOURCE_NOT_FOUND", title="Sucursal no encontrada"
        )

    record, owned = await idempotency.claim(
        tenant_id, "appointments.create_hold", idempotency_key, body.model_dump(mode="json")
    )
    if not owned:
        if str(record["status"]) == "failed":
            response = idempotency_repo.response_body(record)
            raise ProblemException(
                status=int(record["response_status"] or 409),
                code=str(response.get("code", "APPOINTMENT_CONFLICT")),
                title=str(response.get("title", "Horario no disponible")),
                detail=str(response.get("detail", "Ya existe una cita activa que se solapa.")),
            )
        return AppointmentHold.model_validate(idempotency_repo.response_body(record))

    try:
        row = await appts_repo.create_hold(
            tenant_id=tenant_id,
            branch_id=body.branch_id,
            user_id=None if user.is_public else int(user.user_id),
            module_code=body.module_code,
            service_name=body.service_name,
            starts_at=_to_utc(body.starts_at),
            ends_at=_to_utc(body.ends_at),
        )
    except IntegrityError as exc:
        error = {
            "code": "APPOINTMENT_CONFLICT",
            "title": "Horario no disponible",
            "detail": "Ya existe una cita activa que se solapa en esa sucursal.",
        }
        await idempotency_repo.complete(
            int(record["id"]), status="failed", response_status=409, response_body=error
        )
        raise ProblemException(
            status=409,
            code="APPOINTMENT_CONFLICT",
            title="Horario no disponible",
            detail="Ya existe una cita activa que se solapa en esa sucursal.",
        ) from exc

    hold = AppointmentHold(
        appointment_id=ids.encode(ids.APPOINTMENT, row["id"]),
        status=row["status"],
        branch_id=body.branch_id,
        module_code=body.module_code,
        service_name=body.service_name,
        starts_at=row["starts_at"],
        ends_at=row["ends_at"],
        hold_expires_at=row["hold_expires_at"],
    )
    await idempotency_repo.complete(
        int(record["id"]),
        status="succeeded",
        response_status=201,
        response_body=hold.model_dump(mode="json"),
        resource_id=hold.appointment_id,
    )
    return hold
