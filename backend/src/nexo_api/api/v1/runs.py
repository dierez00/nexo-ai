"""Router de runs (delgado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sse_starlette.sse import EventSourceResponse

from nexo_api.api.deps import get_current_user, get_user_or_public, get_user_or_public_sse
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.run import RunSummary
from nexo_api.services.runs import service as runs_service
from nexo_contracts import RunEvent, RunResult

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get(
    "/runs",
    response_model=list[RunSummary],
    summary='Listar mis runs recientes ("mis trámites")',
    responses=problem_responses(401),
)
async def list_runs(
    conversation_id: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: UserProfile = Depends(get_current_user),
) -> list[RunSummary]:
    return await runs_service.list_runs(
        user,
        conversation_id_wire=conversation_id,
        domain=domain,
        status=status,
        limit=limit,
    )


@router.get(
    "/runs/{run_id}",
    response_model=RunResult,
    summary="Snapshot de un run",
    responses=problem_responses(401, 404),
)
async def get_run(
    run_id: str,
    user: UserProfile = Depends(get_user_or_public),
) -> RunResult:
    return await runs_service.get_run(user, run_id)


@router.get(
    "/runs/{run_id}/events/list",
    response_model=list[RunEvent],
    summary="Lista de eventos del run (replay/timeline, no-SSE)",
    responses=problem_responses(401, 404),
)
async def run_events_list(
    run_id: str,
    user: UserProfile = Depends(get_user_or_public),
) -> list[RunEvent]:
    return await runs_service.list_events(user, run_id)


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
    user: UserProfile = Depends(get_user_or_public_sse),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    last_event_id_qs: str | None = Query(default=None, alias="last_event_id"),
) -> EventSourceResponse:
    # El header lo manda el reintento nativo de `EventSource`; el query param es
    # para cuando el propio cliente abre una conexión nueva ya sabiendo desde
    # dónde retomar (recarga de página), caso en el que no hay nada de qué
    # "reconectar" y por tanto el navegador nunca envía el header.
    run_internal, status = await runs_service.get_run_for_stream(user, run_id)
    return EventSourceResponse(
        runs_service.event_stream(
            run_internal, run_id, status, _parse_last_event_id(last_event_id or last_event_id_qs)
        )
    )
