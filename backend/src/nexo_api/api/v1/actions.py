"""Router de acciones (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from nexo_api.api.deps import enforce_rate_limit, get_action_executor
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.action import ConfirmActionRequest
from nexo_api.schemas.auth import UserProfile
from nexo_api.services.actions import ActionExecutor
from nexo_api.services.actions import service as actions_service
from nexo_contracts import ActionResult

router = APIRouter(prefix="/api/v1", tags=["actions"])


@router.post(
    "/actions/{action_id}/confirm",
    response_model=ActionResult,
    summary="Confirmar acción (idempotente)",
    responses=problem_responses(400, 401, 403, 409, 422, 429),
)
async def confirm_action(
    action_id: str,
    body: ConfirmActionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: UserProfile = Depends(enforce_rate_limit),
    executor: ActionExecutor = Depends(get_action_executor),
) -> ActionResult:
    return await actions_service.confirm_action(user, action_id, idempotency_key, body, executor)
