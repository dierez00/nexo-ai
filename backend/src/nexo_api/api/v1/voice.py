"""Router del canal de voz (ElevenLabs Conversational AI) — delgado.

Expone un turno **síncrono** que el agente de voz consume como server-tool:
manda el mensaje, el orquestador resuelve, y la respuesta ya verificada vuelve
en la misma llamada para leerse en voz alta. Ver `docs/elevenlabs_voice_agent.md`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from nexo_api.api.deps import enforce_rate_limit_public, get_orchestrator
from nexo_api.core.config import get_settings
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.voice import VoiceTurnRequest, VoiceTurnResponse
from nexo_api.services.orchestration import Orchestrator
from nexo_api.services.runs import service as runs_service

router = APIRouter(prefix="/api/v1", tags=["voice"])


@router.post(
    "/voice/turn",
    response_model=VoiceTurnResponse,
    summary="Turno de voz síncrono (acceso público)",
    responses=problem_responses(401, 404, 429, 504),
)
async def voice_turn(
    body: VoiceTurnRequest,
    request: Request,
    user: UserProfile = Depends(enforce_rate_limit_public),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> VoiceTurnResponse:
    trace_id: str = request.state.trace_id
    return await runs_service.voice_turn(
        user,
        body,
        trace_id,
        orchestrator,
        get_settings().voice_turn_timeout_seconds,
    )
