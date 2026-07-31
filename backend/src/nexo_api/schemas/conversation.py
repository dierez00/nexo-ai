"""Esquemas de conversaciones y mensajes (§9.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Channel = Literal["web", "whatsapp", "voice", "admin"]


class ConversationCreate(BaseModel):
    channel: Channel = "web"
    title: str | None = None


class Conversation(BaseModel):
    conversation_id: str
    channel: str
    status: str
    title: str | None = None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
