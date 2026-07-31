"""Repositorio de sucursales (solo lo necesario para citas)."""

from __future__ import annotations

from sqlalchemy import text

from nexo_api.repositories._base import read_session


async def exists(tenant_id: int, branch_id: int) -> bool:
    sql = text("select 1 from public.branches where id = :id and tenant_id = :tenant_id")
    async with read_session() as session:
        result = await session.execute(sql, {"id": branch_id, "tenant_id": tenant_id})
        return result.first() is not None
