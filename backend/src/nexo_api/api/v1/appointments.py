"""Router de citas (delgado)."""

from __future__ import annotations

from datetime import date as DateType

from fastapi import APIRouter, Depends, status

from nexo_api.api.deps import get_current_user
from nexo_api.schemas.appointment import AppointmentHold, AppointmentSlot, HoldCreate
from nexo_api.schemas.auth import UserProfile
from nexo_api.services.appointments import service as appointments_service

router = APIRouter(prefix="/api/v1", tags=["appointments"])


@router.get("/appointments/availability", response_model=list[AppointmentSlot])
async def availability(
    branch_id: int,
    module_code: str,
    date: DateType,
    user: UserProfile = Depends(get_current_user),
) -> list[AppointmentSlot]:
    return await appointments_service.get_availability(user, branch_id, module_code, date)


@router.post(
    "/appointments/holds",
    response_model=AppointmentHold,
    status_code=status.HTTP_201_CREATED,
)
async def create_hold(
    body: HoldCreate,
    user: UserProfile = Depends(get_current_user),
) -> AppointmentHold:
    return await appointments_service.create_hold(user, body)
