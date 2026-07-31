"""Router de conversaciones y mensajes (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from nexo_api.api.deps import get_current_user, get_orchestrator
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.conversation import Conversation, ConversationCreate, MessageCreate
from nexo_api.schemas.run import RunAccepted
from nexo_api.services.conversations import service as conversations_service
from nexo_api.services.orchestration import Orchestrator
from nexo_api.services.runs import service as runs_service

router = APIRouter(prefix="/api/v1", tags=["conversations"])


@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    user: UserProfile = Depends(get_current_user),
) -> Conversation:
    return await conversations_service.create_conversation(user, body)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=RunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_message(
    conversation_id: str,
    body: MessageCreate,
    request: Request,
    user: UserProfile = Depends(get_current_user),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> RunAccepted:
    trace_id: str = request.state.trace_id
    return await runs_service.post_message(user, conversation_id, body, trace_id, orchestrator)
