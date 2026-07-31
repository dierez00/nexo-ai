"""Sink de eventos en memoria con secuencia estricta (`DIE-F0-027`).

Equivale al sink real (JSONL primero, persistencia después) en todo lo que
importa para la orquestación: acepta eventos en orden, los devuelve para replay
y rechaza cualquier hueco o retroceso.
"""

from __future__ import annotations

from nexo_contracts import RunEvent

from ..ports.events import EventSequenceError


class InMemoryEventSink:
    """Almacena eventos por run y verifica la monotonía estricta de `sequence`."""

    def __init__(self) -> None:
        self._events: dict[str, list[RunEvent]] = {}

    async def emit(self, event: RunEvent) -> None:
        events = self._events.setdefault(event.run_id, [])
        expected = len(events) + 1
        if event.sequence != expected:
            raise EventSequenceError(event.run_id, expected, event.sequence)
        events.append(event)

    async def read(self, run_id: str, *, after: int = 0) -> tuple[RunEvent, ...]:
        return tuple(e for e in self._events.get(run_id, []) if e.sequence > after)

    async def last_sequence(self, run_id: str) -> int:
        events = self._events.get(run_id, [])
        return events[-1].sequence if events else 0

    def runs(self) -> tuple[str, ...]:
        return tuple(sorted(self._events))

    def types(self, run_id: str) -> tuple[str, ...]:
        """Tipos de evento en orden. Es la forma legible de afirmar sobre una traza."""
        return tuple(event.type.value for event in self._events.get(run_id, []))
