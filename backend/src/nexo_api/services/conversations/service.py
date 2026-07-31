"""Casos de uso de conversaciones."""

from __future__ import annotations

from sqlalchemy import RowMapping

from nexo_api.core import ids
from nexo_api.repositories import conversations as conv_repo
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.conversation import Conversation, ConversationCreate


def _to_conversation(row: RowMapping) -> Conversation:
    return Conversation(
        conversation_id=ids.encode(ids.CONVERSATION, row["id"]),
        channel=row["channel"],
        status=row["status"],
        title=row["title"],
        created_at=row["created_at"],
    )


async def create_conversation(user: UserProfile, body: ConversationCreate) -> Conversation:
    row = await conv_repo.create(
        tenant_id=int(user.tenant_id),
        user_id=None if user.is_public else int(user.user_id),
        channel=body.channel,
        title=body.title,
    )
    return _to_conversation(row)
