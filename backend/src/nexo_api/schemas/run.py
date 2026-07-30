"""Esquemas de runs y eventos (§9.2, §9.11)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

RunStatus = Literal["running", "completed", "failed", "requires_action"]


class Identity(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[str]
    permissions: list[str]


class RunRequest(BaseModel):
    """Lo que el backend envía a la orquestación."""

    run_id: str
    trace_id: str
    conversation_id: str
    user_message: str
    channel: str
    identity: Identity
    locale: str = "es-MX"


class RunEvent(BaseModel):
    """Evento de ejecución en el wire (deriva de public.run_events)."""

    event_id: str
    run_id: str
    trace_id: str
    sequence: int
    type: str
    node_name: str
    timestamp: datetime
    data: dict[str, Any] = Field(default_factory=dict)


class RunResult(BaseModel):
    """Snapshot de un run (§9.11)."""

    run_id: str
    trace_id: str
    status: RunStatus
    answer: str | None = None
    domain: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    available_actions: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class RunAccepted(BaseModel):
    """Respuesta 202 al postear un mensaje."""

    run_id: str
    trace_id: str
    status: RunStatus
    events_url: str
    created_at: datetime
