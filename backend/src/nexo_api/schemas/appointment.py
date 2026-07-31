"""Esquemas de citas (§9.2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, model_validator


class AppointmentSlot(BaseModel):
    starts_at: datetime
    ends_at: datetime
    available: bool


class HoldCreate(BaseModel):
    branch_id: int
    module_code: str
    service_name: str
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def _check_range(self) -> HoldCreate:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at debe ser posterior a starts_at")
        return self


class AppointmentHold(BaseModel):
    appointment_id: str
    status: str
    branch_id: int
    module_code: str
    service_name: str
    starts_at: datetime
    ends_at: datetime
    hold_expires_at: datetime
