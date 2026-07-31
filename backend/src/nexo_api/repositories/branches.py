"""Repositorio de sucursales (solo lo necesario para citas)."""

from __future__ import annotations

from sqlalchemy import text

from nexo_api.repositories._base import read_session


async def exists(tenant_id: int, branch_id: int) -> bool:
    sql = text("select 1 from public.branches where id = :id and tenant_id = :tenant_id")
    async with read_session() as session:
        result = await session.execute(sql, {"id": branch_id, "tenant_id": tenant_id})
        return result.first() is not None


async def default_id(tenant_id: int) -> int | None:
    """Sucursal activa por defecto del tenant, para agendar desde el chat.

    En el chat la persona no elige sucursal: la elige el trámite. El MVP tiene
    una sola sucursal activa por tenant; cuando haya varias, esto se sustituye
    por la sucursal declarada en el módulo, no por otra heurística.
    """
    sql = text("""
        select id from public.branches
        where tenant_id = :tenant_id and status = 'active'
        order by id limit 1
    """)
    async with read_session() as session:
        row = (await session.execute(sql, {"tenant_id": tenant_id})).mappings().first()
        return int(row["id"]) if row is not None else None
