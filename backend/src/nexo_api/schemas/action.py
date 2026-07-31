"""DTO HTTP para confirmar una acción pendiente canónica."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ConfirmActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent: bool = Field(default=False)
    expected_version: int = Field(ge=1)
