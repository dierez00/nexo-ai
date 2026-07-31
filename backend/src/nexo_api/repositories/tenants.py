"""Repositorio de tenants (solo lecturas puntuales)."""

from __future__ import annotations

from sqlalchemy import text

from nexo_api.repositories._base import read_session


async def id_by_slug(slug: str) -> int | None:
    """`id` del tenant por su slug, o ``None`` si no existe."""
    sql = text("select id from public.tenants where slug = :slug")
    async with read_session() as session:
        row = (await session.execute(sql, {"slug": slug})).mappings().first()
        return int(row["id"]) if row is not None else None
