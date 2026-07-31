"""Secuencia de eventos estrictamente monotónica (§7.8).

Un hueco o un retroceso en la secuencia rompe el replay, la reconexión de SSE y
la reconstrucción del workflow. El sink los rechaza en vez de corregirlos en
silencio.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from nexo_contracts import (
    ActorType,
    EventActor,
    EventSequence,
    EventStatus,
    EventType,
    RunEvent,
)
from nexo_orchestration.ports.events import EventSequenceError
from nexo_orchestration.testing import InMemoryEventSink

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


def _event(sequence: int, run_id: str = "run_000001") -> RunEvent:
    return RunEvent(
        event_id=f"evt_{sequence:06d}",
        trace_id="trace_000001",
        run_id=run_id,
        sequence=sequence,
        type=EventType.RUN_STARTED,
        timestamp=NOW,
        actor=EventActor(type=ActorType.SUPERVISOR, name="supervisor"),
        status=EventStatus.SUCCEEDED,
    )


async def test_sink_accepts_consecutive_sequences() -> None:
    sink = InMemoryEventSink()
    for sequence in range(1, 6):
        await sink.emit(_event(sequence))
    assert await sink.last_sequence("run_000001") == 5


async def test_sink_rejects_a_gap() -> None:
    sink = InMemoryEventSink()
    await sink.emit(_event(1))
    with pytest.raises(EventSequenceError) as caught:
        await sink.emit(_event(3))
    assert caught.value.expected == 2
    assert caught.value.received == 3


async def test_sink_rejects_a_repeated_sequence() -> None:
    sink = InMemoryEventSink()
    await sink.emit(_event(1))
    with pytest.raises(EventSequenceError):
        await sink.emit(_event(1))


async def test_sequences_are_independent_per_run() -> None:
    sink = InMemoryEventSink()
    await sink.emit(_event(1, run_id="run_000001"))
    await sink.emit(_event(1, run_id="run_000002"))
    assert await sink.last_sequence("run_000001") == 1
    assert await sink.last_sequence("run_000002") == 1


async def test_read_after_supports_sse_reconnection() -> None:
    sink = InMemoryEventSink()
    for sequence in range(1, 6):
        await sink.emit(_event(sequence))
    resumed = await sink.read("run_000001", after=3)
    assert [event.sequence for event in resumed] == [4, 5]


def test_event_sequence_contract_rejects_disorder() -> None:
    """El contrato también lo verifica: un replay no puede recibir desorden."""
    with pytest.raises(ValidationError, match="secuencia rota"):
        EventSequence(run_id="run_000001", events=[_event(1), _event(3)])


def test_failed_event_requires_an_error() -> None:
    with pytest.raises(ValidationError, match="sin error normalizado"):
        RunEvent(
            event_id="evt_000001",
            trace_id="trace_000001",
            run_id="run_000001",
            sequence=1,
            type=EventType.RUN_FAILED,
            timestamp=NOW,
            actor=EventActor(type=ActorType.SUPERVISOR, name="supervisor"),
            status=EventStatus.FAILED,
        )
