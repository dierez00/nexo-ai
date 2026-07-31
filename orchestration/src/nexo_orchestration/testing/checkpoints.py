"""Almacén de checkpoints en memoria (`DIE-F0-027`).

Guarda una copia **serializada** del estado, no la instancia viva. Es la
diferencia que hace que este doble sea equivalente al almacén real: si el estado
contuviera algo no serializable, guardarlo fallaría aquí igual que fallaría en
PostgreSQL, en vez de "funcionar" en pruebas y romperse en integración.
"""

from __future__ import annotations

from nexo_contracts import RunState

from ..ports.checkpoints import CheckpointError


class InMemoryCheckpointStore:
    """Checkpoints por run, con historial de nodos confirmados."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, list[tuple[str, str]]] = {}

    async def save(self, state: RunState, *, node: str, checkpoint_id: str) -> str:
        del node  # el nodo ya viaja dentro de `state.completed_nodes`
        try:
            payload = state.model_dump_json()
        except Exception as exc:
            raise CheckpointError(
                f"el estado del run {state.run_id} no es serializable y no puede guardarse: {exc}"
            ) from exc

        self._checkpoints.setdefault(state.run_id, []).append((checkpoint_id, payload))
        return checkpoint_id

    async def load(self, run_id: str) -> RunState | None:
        entries = self._checkpoints.get(run_id)
        if not entries:
            return None
        _, payload = entries[-1]
        return RunState.model_validate_json(payload)

    async def history(self, run_id: str) -> tuple[str, ...]:
        return tuple(checkpoint_id for checkpoint_id, _ in self._checkpoints.get(run_id, []))

    async def load_at(self, run_id: str, checkpoint_id: str) -> RunState | None:
        """Estado en un checkpoint concreto, para probar reanudación desde el medio."""
        for stored_id, payload in self._checkpoints.get(run_id, []):
            if stored_id == checkpoint_id:
                return RunState.model_validate_json(payload)
        return None
