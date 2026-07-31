"""Router de acciones (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from nexo_api.api.deps import get_action_executor, get_current_user
from nexo_api.schemas.action import ActionResult, ConfirmActionRequest
from nexo_api.schemas.auth import UserProfile
from nexo_api.services.actions import ActionExecutor
from nexo_api.services.actions import service as actions_service

router = APIRouter(prefix="/api/v1", tags=["actions"])


@router.post("/actions/{action_id}/confirm", response_model=ActionResult)
async def confirm_action(
    action_id: str,
    body: ConfirmActionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: UserProfile = Depends(get_current_user),
    executor: ActionExecutor = Depends(get_action_executor),
) -> ActionResult:
    return await actions_service.confirm_action(user, action_id, idempotency_key, body, executor)
