"""Catálogo operativo desde la base (tenant-scoped donde aplica)."""

from __future__ import annotations

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import read_session


async def modules(tenant_id: int) -> list[RowMapping]:
    """Módulos con su estado (enabled) para el tenant."""
    sql = text("""
        select m.code, m.name, m.is_core,
               coalesce(tm.status = 'enabled', false) as enabled
        from public.modules m
        left join public.tenant_modules tm
            on tm.module_id = m.id and tm.tenant_id = :tenant_id
        order by m.id
    """)
    async with read_session() as session:
        return list((await session.execute(sql, {"tenant_id": tenant_id})).mappings().all())


async def roles(tenant_id: int) -> list[RowMapping]:
    """Roles de sistema (tenant_id null) y del propio tenant."""
    sql = text("""
        select code, name, is_system from public.roles
        where tenant_id is null or tenant_id = :tenant_id
        order by id
    """)
    async with read_session() as session:
        return list((await session.execute(sql, {"tenant_id": tenant_id})).mappings().all())


async def permissions() -> list[RowMapping]:
    sql = text("""
        select p.code, m.code as module_code
        from public.permissions p
        join public.modules m on m.id = p.module_id
        order by p.code
    """)
    async with read_session() as session:
        return list((await session.execute(sql)).mappings().all())
