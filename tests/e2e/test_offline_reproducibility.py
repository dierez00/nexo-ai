"""Reproducibilidad de la ruta offline (§7.8, gate §7.9).

Dos ejecuciones con el mismo reloj, los mismos IDs y el mismo guion de modelo
deben producir bytes idénticos. Sin esta propiedad, comparar un baseline entre
commits no significa nada: cualquier diff podría ser ruido.

Ninguna prueba de este archivo abre red, base de datos ni credenciales.
"""

from __future__ import annotations

import json

import pytest

from nexo_contracts import Channel, Identity, RunRequest, RunStatus
from nexo_orchestration.configuration import load_config
from nexo_orchestration.graph import MinimalGraph
from nexo_orchestration.testing import (
    FakeChatModel,
    FrozenClock,
    InMemoryCheckpointStore,
    InMemoryEventSink,
    Scenario,
    SequentialIdFactory,
)

pytestmark = pytest.mark.e2e


def _build() -> tuple[MinimalGraph, InMemoryEventSink, FrozenClock]:
    clock = FrozenClock()
    sink = InMemoryEventSink()
    graph = MinimalGraph(
        model=FakeChatModel(
            {"classify_request": Scenario(data={"domain": "vehiculos", "confidence": 0.91})}
        ),
        event_sink=sink,
        checkpoints=InMemoryCheckpointStore(),
        clock=clock,
        ids=SequentialIdFactory(),
        policies=load_config().policies,
    )
    return graph, sink, clock


def _request(clock: FrozenClock) -> RunRequest:
    return RunRequest(
        run_id="run_000001",
        trace_id="trace_000001",
        conversation_id="conv_000001",
        user_message="Quiero renovar mi licencia y saber si debo algo",
        channel=Channel.WEB,
        identity=Identity(
            user_id="usr_demo",
            institution_id="inst_demo",
            roles=["citizen"],
            permissions=["domain:vehiculos:read"],
        ),
        received_at=clock.now(),
    )


async def _run_once() -> tuple[str, list[dict]]:
    graph, sink, clock = _build()
    result = await graph.invoke(_request(clock))
    events = [json.loads(event.model_dump_json()) for event in await sink.read("run_000001")]
    return result.model_dump_json(), events


async def test_two_runs_produce_identical_results() -> None:
    first_result, _ = await _run_once()
    second_result, _ = await _run_once()
    assert first_result == second_result


async def test_two_runs_produce_identical_event_traces() -> None:
    _, first_events = await _run_once()
    _, second_events = await _run_once()
    assert first_events == second_events


async def test_ids_are_reproducible_across_runs() -> None:
    _, first_events = await _run_once()
    _, second_events = await _run_once()
    assert [event["event_id"] for event in first_events] == [
        event["event_id"] for event in second_events
    ]


async def test_run_is_fully_reconstructible_by_trace_id() -> None:
    """Gate §7.9: el run emite eventos válidos y reanudables."""
    graph, sink, clock = _build()
    result = await graph.invoke(_request(clock))
    events = await sink.read("run_000001")

    assert result.status is RunStatus.SUCCEEDED
    assert {event.trace_id for event in events} == {"trace_000001"}
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    # La traza contiene el ciclo completo: encolado, clasificación y cierre.
    types = {event.type.value for event in events}
    assert {"run.queued", "classification.completed", "run.completed"} <= types


async def test_offline_profile_needs_no_provider_alias_enabled() -> None:
    """El alias offline debe existir y estar habilitado sin credenciales."""
    router = load_config().model_router
    offline = next(entry for entry in router.aliases if entry.alias == router.offline_alias)
    assert offline.enabled is True
    assert offline.provider_ref.api_key_ref is None
