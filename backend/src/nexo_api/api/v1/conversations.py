"""Router de conversaciones y mensajes (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from nexo_api.api.deps import (
    enforce_rate_limit_public,
    get_current_user,
    get_orchestrator,
    get_run_task_manager,
    get_user_or_public,
)
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.conversation import Conversation, ConversationCreate, MessageCreate
from nexo_api.schemas.run import RunAccepted
from nexo_api.services.conversations import service as conversations_service
from nexo_api.services.orchestration import Orchestrator
from nexo_api.services.runs import service as runs_service
from nexo_api.services.runs.tasks import RunTaskManager

router = APIRouter(prefix="/api/v1", tags=["conversations"])


@router.post(
    "/conversations",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
    summary="Crear conversación (acceso público)",
    responses=problem_responses(401),
)
async def create_conversation(
    body: ConversationCreate,
    user: UserProfile = Depends(get_user_or_public),
) -> Conversation:
    return await conversations_service.create_conversation(user, body)


@router.get(
    "/conversations",
    response_model=list[Conversation],
    summary="Listar mis conversaciones más recientes",
    responses=problem_responses(401),
)
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    user: UserProfile = Depends(get_current_user),
) -> list[Conversation]:
    return await conversations_service.list_conversations(user, limit)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=RunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Postear mensaje y ejecutar un run (acceso público)",
    responses=problem_responses(401, 404, 429),
)
async def post_message(
    conversation_id: str,
    body: MessageCreate,
    request: Request,
    user: UserProfile = Depends(enforce_rate_limit_public),
    orchestrator: Orchestrator = Depends(get_orchestrator),
    task_manager: RunTaskManager = Depends(get_run_task_manager),
) -> RunAccepted:
    trace_id: str = request.state.trace_id
    return await runs_service.post_message(
        user, conversation_id, body, trace_id, orchestrator, task_manager
    )
