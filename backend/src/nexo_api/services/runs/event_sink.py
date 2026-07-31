"""Adaptador PostgreSQL del ``EventSinkPort`` de orquestación."""

from __future__ import annotations

from nexo_api.core import ids
from nexo_api.repositories import run_events as events_repo
from nexo_contracts import EventSequence, RunEvent
from nexo_orchestration.ports.events import EventSequenceError


class PostgresEventSink:
    async def emit(self, event: RunEvent) -> None:
        run_id = ids.decode(ids.RUN, event.run_id)
        expected = await events_repo.last_sequence(run_id) + 1
        if event.sequence != expected:
            raise EventSequenceError(event.run_id, expected, event.sequence)
        await events_repo.create(event)

    async def read(self, run_id: str, *, after: int = 0) -> tuple[RunEvent, ...]:
        internal_id = ids.decode(ids.RUN, run_id)
        events = tuple(
            events_repo.to_contract(row, run_id)
            for row in await events_repo.list_after(internal_id)
        )
        return EventSequence(run_id=run_id, events=list(events)).since(after)

    async def last_sequence(self, run_id: str) -> int:
        return await events_repo.last_sequence(ids.decode(ids.RUN, run_id))
