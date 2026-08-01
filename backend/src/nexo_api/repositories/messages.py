"""Repositorio de mensajes."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from nexo_api.repositories._base import dump_json, uow


async def create(
    conversation_id: int,
    sender_type: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    sql = text("""
        insert into public.messages (conversation_id, sender_type, content, metadata)
        values (:conversation_id, :sender_type, :content, cast(:metadata as jsonb))
        returning id
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {
                "conversation_id": conversation_id,
                "sender_type": sender_type,
                "content": content,
                "metadata": dump_json(metadata or {}),
            },
        )
        return int(result.scalar_one())


async def set_delivery_status(provider_message_id: str, status: str) -> None:
    """Marca el estado de entrega en metadata (best-effort; no-op si no hay match)."""
    sql = text("""
        update public.messages
        set metadata = jsonb_set(
            coalesce(metadata, '{}'::jsonb), '{delivery_status}', to_jsonb(cast(:status as text))
        )
        where metadata->>'provider_message_id' = :pmid
    """)
    async with uow() as session:
        await session.execute(sql, {"status": status, "pmid": provider_message_id})


async def exists_provider_message(conversation_id: int, provider_message_id: str) -> bool:
    """Dedup de webhooks: ¿ya existe un mensaje con este provider_message_id?"""
    sql = text("""
        select 1 from public.messages
        where conversation_id = :conversation_id
          and metadata->>'provider_message_id' = :pmid
        limit 1
    """)
    async with uow() as session:
        result = await session.execute(
            sql, {"conversation_id": conversation_id, "pmid": provider_message_id}
        )
        return result.first() is not None
