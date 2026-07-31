"""Repositorio de citas. El constraint GiST `appointments_no_overlap` (Daher)
garantiza a nivel de BD que no haya solapamientos de citas activas."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import read_session, uow


async def list_active_in_range(
    tenant_id: int, branch_id: int, start: datetime, end: datetime
) -> list[RowMapping]:
    """Citas activas (hold/confirmed) que solapan el rango dado."""
    sql = text("""
        select lower(time_range) as starts_at, upper(time_range) as ends_at
        from public.appointments
        where tenant_id = :tenant_id and branch_id = :branch_id
          and status in ('hold', 'confirmed')
          and time_range && tstzrange(:start, :end, '[)')
        order by starts_at
    """)
    async with read_session() as session:
        result = await session.execute(
            sql, {"tenant_id": tenant_id, "branch_id": branch_id, "start": start, "end": end}
        )
        return list(result.mappings().all())


async def create_hold(
    tenant_id: int,
    branch_id: int,
    user_id: int | None,
    module_code: str,
    service_name: str,
    starts_at: datetime,
    ends_at: datetime,
) -> RowMapping:
    """Inserta un hold. Si solapa una cita activa, el GiST lanza IntegrityError."""
    sql = text("""
        insert into public.appointments
            (tenant_id, branch_id, user_id, module_code, service_name, time_range, status)
        values
            (:tenant_id, :branch_id, :user_id, :module_code, :service_name,
             tstzrange(:starts_at, :ends_at, '[)'), 'hold')
        returning id, status, hold_expires_at,
                  lower(time_range) as starts_at, upper(time_range) as ends_at
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "branch_id": branch_id,
                "user_id": user_id,
                "module_code": module_code,
                "service_name": service_name,
                "starts_at": starts_at,
                "ends_at": ends_at,
            },
        )
        return result.mappings().one()
