"""Router de runs (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from nexo_api.api.deps import get_current_user, get_current_user_sse
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.run import RunResult
from nexo_api.services.runs import service as runs_service

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get("/runs/{run_id}", response_model=RunResult)
async def get_run(
    run_id: str,
    user: UserProfile = Depends(get_current_user),
) -> RunResult:
    return await runs_service.get_run(user, run_id)


def _parse_last_event_id(request: Request) -> int:
    raw = request.headers.get("Last-Event-ID", "")
    try:
        return int(raw)
    except ValueError:
        return 0


@router.get("/runs/{run_id}/events")
async def run_events(
    run_id: str,
    request: Request,
    user: UserProfile = Depends(get_current_user_sse),
) -> EventSourceResponse:
    run_internal, status = await runs_service.get_run_for_stream(user, run_id)
    last_event_id = _parse_last_event_id(request)
    return EventSourceResponse(
        runs_service.event_stream(run_internal, run_id, status, last_event_id)
    )
