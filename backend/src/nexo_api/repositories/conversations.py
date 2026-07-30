"""Repositorio de conversaciones. Toda query filtra por tenant_id (bypass RLS)."""

from __future__ import annotations

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import read_session, uow

_COLS = "id, channel, status, title, created_at"


async def create(
    tenant_id: int, user_id: int | None, channel: str, title: str | None
) -> RowMapping:
    sql = text(f"""
        insert into public.conversations (tenant_id, user_id, channel, title)
        values (:tenant_id, :user_id, :channel, :title)
        returning {_COLS}
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {"tenant_id": tenant_id, "user_id": user_id, "channel": channel, "title": title},
        )
        return result.mappings().one()


async def get(tenant_id: int, conversation_id: int) -> RowMapping | None:
    sql = text(
        f"select {_COLS} from public.conversations where id = :id and tenant_id = :tenant_id"
    )
    async with read_session() as session:
        result = await session.execute(sql, {"id": conversation_id, "tenant_id": tenant_id})
        return result.mappings().first()
