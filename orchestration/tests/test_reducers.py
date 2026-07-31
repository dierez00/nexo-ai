"""Reducers deterministas y sin mutación compartida (`DIE-F0-039`).

El merge debe dar el mismo resultado sin importar el orden de llegada. Es lo que
permitirá, en Fase 4, que el verificador y el estimador terminen en cualquier
orden sin cambiar la respuesta.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from nexo_contracts import (
    CandidateFact,
    Channel,
    Domain,
    FactCategory,
    FactOrigin,
    FactValue,
    Identity,
    RunRequest,
    RunState,
    RunStatus,
)
from nexo_orchestration.reducers import (
    merge_candidate_facts,
    merge_run_state,
    merge_warnings,
)

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


def _fact(fact_id: str) -> CandidateFact:
    return CandidateFact(
        fact_id=fact_id,
        claim=f"claim de {fact_id}",
        value=FactValue(text="valor"),
        category=FactCategory.CONTEXT,
        domain=Domain.VEHICULOS,
        origin=FactOrigin.USER,
        confidence=0.5,
    )


def _state(**overrides) -> RunState:
    request = RunRequest(
        run_id="run_000001",
        trace_id="trace_000001",
        conversation_id="conv_000001",
        user_message="hola",
        channel=Channel.WEB,
        identity=Identity(user_id="usr_demo", institution_id="inst_demo", roles=["citizen"]),
        received_at=NOW,
    )
    payload = {
        "run_id": request.run_id,
        "trace_id": request.trace_id,
        "conversation_id": request.conversation_id,
        "request": request,
        "created_at": NOW,
        "updated_at": NOW,
    }
    payload.update(overrides)
    return RunState(**payload)


def test_fact_merge_is_order_independent() -> None:
    left, right = [_fact("fact_b"), _fact("fact_a")], [_fact("fact_c")]
    assert merge_candidate_facts(left, right) == merge_candidate_facts(right, left)


def test_fact_merge_deduplicates_by_id() -> None:
    merged = merge_candidate_facts([_fact("fact_a")], [_fact("fact_a"), _fact("fact_b")])
    assert [fact.fact_id for fact in merged] == ["fact_a", "fact_b"]


def test_warning_merge_is_order_independent_and_deduplicated() -> None:
    assert merge_warnings(["b", "a"], ["a", "c"]) == ["a", "b", "c"]


def test_state_merge_does_not_mutate_its_inputs() -> None:
    current = _state(candidate_facts=[_fact("fact_a")], warnings=["w1"])
    update = _state(candidate_facts=[_fact("fact_b")], warnings=["w2"])
    snapshot_current = current.model_dump_json()
    snapshot_update = update.model_dump_json()

    merge_run_state(current, update)

    assert current.model_dump_json() == snapshot_current
    assert update.model_dump_json() == snapshot_update


def test_state_merge_consolidates_accumulators() -> None:
    current = _state(candidate_facts=[_fact("fact_a")], warnings=["w1"], completed_nodes=["start"])
    update = _state(
        candidate_facts=[_fact("fact_b")],
        warnings=["w2"],
        completed_nodes=["classify_fake"],
        status=RunStatus.RUNNING,
    )
    merged = merge_run_state(current, update)

    assert [fact.fact_id for fact in merged.candidate_facts] == ["fact_a", "fact_b"]
    assert merged.warnings == ["w1", "w2"]
    assert merged.completed_nodes == ["classify_fake", "start"]
    # Los escalares vienen del update: es la visión más reciente.
    assert merged.status is RunStatus.RUNNING


def test_state_merge_is_order_independent_for_accumulators() -> None:
    left = _state(candidate_facts=[_fact("fact_a")], warnings=["a"])
    right = _state(candidate_facts=[_fact("fact_b")], warnings=["b"])

    forward = merge_run_state(left, right)
    backward = merge_run_state(right, left)

    assert [f.fact_id for f in forward.candidate_facts] == [
        f.fact_id for f in backward.candidate_facts
    ]
    assert forward.warnings == backward.warnings


def test_event_cursor_never_goes_backwards() -> None:
    current = _state(event_cursor=9)
    update = _state(event_cursor=4)
    assert merge_run_state(current, update).event_cursor == 9


def test_states_of_different_runs_cannot_be_merged() -> None:
    with pytest.raises(ValueError, match="runs distintos"):
        merge_run_state(_state(), _state(run_id="run_000002"))
