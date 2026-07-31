"""Router de runs (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sse_starlette.sse import EventSourceResponse

from nexo_api.api.deps import get_current_user, get_current_user_sse
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.run import RunResult
from nexo_api.services.runs import service as runs_service

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get(
    "/runs/{run_id}",
    response_model=RunResult,
    summary="Snapshot de un run",
    responses=problem_responses(401, 404),
)
async def get_run(
    run_id: str,
    user: UserProfile = Depends(get_current_user),
) -> RunResult:
    return await runs_service.get_run(user, run_id)


def _parse_last_event_id(raw: str | None) -> int:
    try:
        return int(raw) if raw else 0
    except ValueError:
        return 0


@router.get(
    "/runs/{run_id}/events",
    summary="Stream SSE de eventos del run",
    responses={
        200: {
            "description": "Stream de RunEvent (text/event-stream), reanudable por Last-Event-ID.",
            "content": {"text/event-stream": {}},
        },
        **problem_responses(401, 404),
    },
)
async def run_events(
    run_id: str,
    user: UserProfile = Depends(get_current_user_sse),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> EventSourceResponse:
    run_internal, status = await runs_service.get_run_for_stream(user, run_id)
    return EventSourceResponse(
        runs_service.event_stream(run_internal, run_id, status, _parse_last_event_id(last_event_id))
    )
