"""Reducers deterministas del estado del run (`DIE-F0-039`).

Dos propiedades sostienen todo lo demás:

1. **Sin mutación compartida.** Cada reducer devuelve un objeto nuevo. Ningún
   nodo modifica el estado que recibió, así que dos ramas que parten del mismo
   checkpoint no pueden pisarse (necesario para el fan-out de Fase 4).
2. **Orden determinista.** Consolidar A y luego B produce el mismo resultado que
   consolidar B y luego A. Sin esto, una carrera entre el verificador y el
   estimador produciría respuestas distintas según quién terminara primero.

Los reducers viven aquí y no en `contracts` a propósito: son mecánica de
orquestación, y los contratos no deben conocer el framework del grafo.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

from nexo_contracts import (
    TERMINAL_RUN_STATUSES,
    CandidateFact,
    Contradiction,
    RunState,
)


def merge_unique[T](
    left: Sequence[T],
    right: Sequence[T],
    *,
    key: Callable[[T], str],
) -> list[T]:
    """Une dos secuencias deduplicando por clave y ordenando por ella.

    El orden por clave, y no por llegada, es lo que hace el merge independiente
    del orden de finalización de las ramas.
    """
    combined: dict[str, T] = {}
    for item in list(left) + list(right):
        combined.setdefault(key(item), item)
    return [combined[k] for k in sorted(combined)]


def merge_candidate_facts(
    left: Sequence[CandidateFact], right: Sequence[CandidateFact]
) -> list[CandidateFact]:
    """Consolida hechos candidatos por `fact_id`, con orden estable."""
    return merge_unique(left, right, key=lambda fact: fact.fact_id)


def merge_contradictions(
    left: Sequence[Contradiction], right: Sequence[Contradiction]
) -> list[Contradiction]:
    return merge_unique(left, right, key=lambda item: item.contradiction_id)


def merge_warnings(left: Iterable[str], right: Iterable[str]) -> list[str]:
    """Deduplica y ordena los warnings; un warning repetido no aporta información."""
    return sorted(set(left) | set(right))


def merge_completed_nodes(left: Iterable[str], right: Iterable[str]) -> list[str]:
    """Nodos confirmados. Se ordenan para que el estado serializado sea comparable."""
    return sorted(set(left) | set(right))


def merge_run_state(current: RunState, update: RunState) -> RunState:
    """Reducer del estado completo, usado por el grafo en cada transición.

    `update` es el estado que produjo un nodo. Los campos escalares se toman del
    update (es la visión más reciente); las colecciones acumulativas se
    consolidan con las reglas de arriba, para que reanudar o consolidar ramas no
    pierda lo que ya se sabía.
    """
    if current.run_id != update.run_id:
        raise ValueError(
            f"no se pueden consolidar estados de runs distintos: "
            f"{current.run_id!r} y {update.run_id!r}"
        )

    # El cursor de eventos nunca retrocede: es la posición real de la traza.
    event_cursor = max(current.event_cursor, update.event_cursor)

    return update.model_copy(
        update={
            "candidate_facts": merge_candidate_facts(
                current.candidate_facts, update.candidate_facts
            ),
            "contradictions": merge_contradictions(
                current.contradictions, update.contradictions
            ),
            "warnings": merge_warnings(current.warnings, update.warnings),
            "completed_nodes": merge_completed_nodes(
                current.completed_nodes, update.completed_nodes
            ),
            "attempts": {**current.attempts, **update.attempts},
            "model_invocations": [*current.model_invocations, *update.model_invocations],
            "event_cursor": event_cursor,
        }
    )


def is_terminal(state: RunState) -> bool:
    return state.status in TERMINAL_RUN_STATUSES
