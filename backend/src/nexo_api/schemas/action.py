"""Esquemas de acciones y confirmación (§9.2, §13)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConfirmActionRequest(BaseModel):
    consent: bool = False
    input: dict[str, Any] = Field(default_factory=dict)
    expected_version: int | None = None


class ActionResult(BaseModel):
    action_id: str
    idempotency_key: str
    action_name: str
    status: str
    folio: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
