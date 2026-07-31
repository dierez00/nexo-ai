"""Repositorio de conversaciones. Toda query filtra por tenant_id (bypass RLS)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, read_session, uow

_COLS = "id, channel, status, title, created_at"


async def create(
    tenant_id: int,
    user_id: int | None,
    channel: str,
    title: str | None,
    metadata: dict[str, Any] | None = None,
) -> RowMapping:
    sql = text(f"""
        insert into public.conversations (tenant_id, user_id, channel, title, metadata)
        values (:tenant_id, :user_id, :channel, :title, cast(:metadata as jsonb))
        returning {_COLS}
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "channel": channel,
                "title": title,
                "metadata": dump_json(metadata or {}),
            },
        )
        return result.mappings().one()


async def find_by_channel_ref(tenant_id: int, channel: str, from_ref: str) -> RowMapping | None:
    """Última conversación activa de un remitente de canal (ej. WhatsApp por pii_ref)."""
    sql = text(f"""
        select {_COLS} from public.conversations
        where tenant_id = :tenant_id and channel = :channel and status = 'active'
          and metadata->>'from_ref' = :from_ref
        order by id desc
        limit 1
    """)
    async with read_session() as session:
        result = await session.execute(
            sql, {"tenant_id": tenant_id, "channel": channel, "from_ref": from_ref}
        )
        return result.mappings().first()


async def get(tenant_id: int, conversation_id: int) -> RowMapping | None:
    sql = text(
        f"select {_COLS} from public.conversations where id = :id and tenant_id = :tenant_id"
    )
    async with read_session() as session:
        result = await session.execute(sql, {"id": conversation_id, "tenant_id": tenant_id})
        return result.mappings().first()
