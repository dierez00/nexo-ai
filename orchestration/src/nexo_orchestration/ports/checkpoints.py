"""Puerto del almacén de checkpoints (`DIE-F0-021`, `DIE-F0-027`).

Guarda `RunState` completo tras cada transición significativa. La implementación
real vivirá en PostgreSQL (responsabilidad de Daher); la de Fase 0 vive en
memoria. Ambas comparten esta interfaz y la misma invariante: solo se guarda
estado serializable.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nexo_contracts import RunState


class CheckpointError(Exception):
    """El estado no pudo persistirse o recuperarse."""


@runtime_checkable
class CheckpointStorePort(Protocol):
    """Persistencia de estado reanudable."""

    async def save(self, state: RunState, *, node: str, checkpoint_id: str) -> str:
        """Guarda un checkpoint tras completar `node` y devuelve su identificador.

        El identificador lo provee quien llama, desde la `IdFactory` inyectada,
        para que sea reproducible y para que el evento `checkpoint.saved` pueda
        emitirse **antes** de persistir. Ese orden es lo que garantiza que el
        `event_cursor` del estado guardado coincida con los eventos realmente
        emitidos; si se guardara primero, una reanudación reutilizaría una
        posición de secuencia ya ocupada.

        Debe verificar que el estado sea serializable antes de aceptarlo: un
        checkpoint que no se puede leer de vuelta no es un checkpoint.
        """
        ...

    async def load(self, run_id: str) -> RunState | None:
        """Último estado guardado del run, o `None` si no existe."""
        ...

    async def history(self, run_id: str) -> tuple[str, ...]:
        """Identificadores de checkpoint del run, en orden cronológico."""
        ...
