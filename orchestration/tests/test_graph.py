"""Grafo mínimo: recorrido, fallos, deadline, checkpoint y reanudación (§7.8)."""

from __future__ import annotations

import pytest

from nexo_contracts import ErrorCode, RunStatus
from nexo_orchestration.graph import NODE_CLASSIFY, NODE_FINALIZE, NODE_START
from nexo_orchestration.testing import FakeBehavior, Scenario

pytestmark = pytest.mark.unit


async def test_fake_model_traverses_the_minimal_graph(graph, request_factory, event_sink):
    """Gate §7.9: un modelo falso recorre el grafo mínimo."""
    result = await graph.invoke(request_factory())

    assert result.status is RunStatus.SUCCEEDED
    assert result.answer
    assert result.metrics.model_invocation_count == 1

    types = event_sink.types("run_000001")
    assert types[0] == "run.queued"
    assert "classification.completed" in types
    assert types[-2:] == ("run.completed", "checkpoint.saved")


async def test_events_are_strictly_sequential(graph, request_factory, event_sink):
    await graph.invoke(request_factory())
    events = await event_sink.read("run_000001")
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))


async def test_every_event_carries_the_policy_version(graph, request_factory, event_sink):
    """`DIE-F0-037`: la versión de políticas se propaga a la traza."""
    await graph.invoke(request_factory())
    events = await event_sink.read("run_000001")
    assert {event.policy_version for event in events} == {"policies-2026-07-30"}


async def test_checkpoint_saved_after_each_node(graph, request_factory, checkpoints):
    """`DIE-F0-041`: una transición significativa deja checkpoint."""
    await graph.invoke(request_factory())
    assert len(await checkpoints.history("run_000001")) == 3


async def test_checkpoint_holds_the_completed_nodes(graph, request_factory, checkpoints):
    await graph.invoke(request_factory())
    state = await checkpoints.load("run_000001")
    assert state is not None
    assert set(state.completed_nodes) == {NODE_START, NODE_CLASSIFY, NODE_FINALIZE}


async def test_checkpoint_cursor_matches_the_emitted_events(
    graph, request_factory, checkpoints, event_sink
):
    """Regresión: el checkpoint no puede quedar atrás de la traza.

    Si el estado se guardara antes de emitir `checkpoint.saved`, su
    `event_cursor` quedaría una posición corta y la reanudación reutilizaría una
    secuencia ya ocupada.
    """
    await graph.invoke(request_factory())
    state = await checkpoints.load("run_000001")
    assert state is not None
    assert state.event_cursor == await event_sink.last_sequence("run_000001")


async def test_resume_does_not_replay_completed_nodes(
    graph, request_factory, checkpoints, model, event_sink
):
    """`DIE-F0-042`: reanudar no reejecuta lo que ya estaba confirmado."""
    await graph.invoke(request_factory())
    invocations_before = model.call_count("classify_request")

    result = await graph.resume("run_000001")

    assert result.status is RunStatus.SUCCEEDED
    # El modelo no se volvió a invocar: la clasificación ya estaba confirmada.
    assert model.call_count("classify_request") == invocations_before

    resumed_events = [
        event for event in await event_sink.read("run_000001") if event.type.value == "run.resumed"
    ]
    assert {event.data["node"] for event in resumed_events} == {
        NODE_START,
        NODE_CLASSIFY,
        NODE_FINALIZE,
    }


async def test_resume_continues_the_event_sequence(graph, request_factory, event_sink):
    """La secuencia sigue donde quedó: el cursor viaja en el estado, no en el emisor."""
    await graph.invoke(request_factory())
    before = await event_sink.last_sequence("run_000001")

    await graph.resume("run_000001")

    events = await event_sink.read("run_000001")
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert await event_sink.last_sequence("run_000001") > before


async def test_resume_without_checkpoint_fails_loudly(graph):
    with pytest.raises(LookupError):
        await graph.resume("run_999999")


async def test_deadline_produces_a_normalized_error(graph, request_factory, clock, event_sink):
    """`DIE-F0-043`: agotar el deadline produce un error normalizado, no una traza rota."""
    request = request_factory()
    clock.advance(request.budgets.deadline_ms + 1)

    result = await graph.invoke(request)

    assert result.error is not None
    assert result.error.code is ErrorCode.RUN_TIMEOUT
    # `RUN_TIMEOUT` está en `partial_on`: el run se degrada, no se declara fallido.
    assert result.status is RunStatus.PARTIAL
    assert "run.partial" in event_sink.types("run_000001")


async def test_model_failure_degrades_the_run(model, graph, request_factory):
    model.program("classify_request", Scenario(behavior=FakeBehavior.PROVIDER_DOWN))
    result = await graph.invoke(request_factory())

    assert result.status is RunStatus.FAILED
    assert result.error is not None
    assert result.error.code is ErrorCode.MODEL_UNAVAILABLE


async def test_invalid_model_output_is_detected(model, graph, request_factory):
    """Una salida que no cumple el contrato se detecta, no se propaga."""
    model.program("classify_request", Scenario(data={"domain": "dominio_inexistente"}))
    result = await graph.invoke(request_factory())

    assert result.status is RunStatus.FAILED
    assert result.error is not None
    assert result.error.code is ErrorCode.MODEL_OUTPUT_INVALID


async def test_failed_run_is_not_finalized_as_successful(model, graph, request_factory):
    """Llegar al final del grafo no convierte un fallo en éxito."""
    model.program("classify_request", Scenario(behavior=FakeBehavior.TIMEOUT))
    result = await graph.invoke(request_factory())
    assert result.status is not RunStatus.SUCCEEDED
    assert result.answer is None


async def test_run_result_hides_internal_state(graph, request_factory):
    """`DIE-F0-044`: el resultado no expone el andamiaje de la ejecución."""
    result = await graph.invoke(request_factory())
    payload = result.model_dump_json()
    for internal in ("completed_nodes", "attempts", "model_invocations", "candidate_facts"):
        assert internal not in payload


async def test_state_stays_serializable_through_the_whole_run(graph, request_factory, checkpoints):
    """`DIE-F0-015`: el estado guardado se relee sin pérdida."""
    await graph.invoke(request_factory())
    state = await checkpoints.load("run_000001")
    assert state is not None
    state.assert_serializable()
    assert state.model_validate_json(state.model_dump_json()) == state
