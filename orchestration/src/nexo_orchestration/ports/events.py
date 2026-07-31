"""Puerto del sink de eventos (`DIE-F0-021`, `DIE-F0-027`).

El sink es el guardián de la secuencia: acepta un evento solo si continúa
exactamente donde quedó el run. Un hueco o un retroceso no se corrige en
silencio, se rechaza — un workflow reconstruido a partir de eventos desordenados
sería una explicación falsa de lo que ocurrió.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nexo_contracts import RunEvent


class EventSequenceError(Exception):
    """La secuencia recibida rompe la monotonía estricta del run."""

    def __init__(self, run_id: str, expected: int, received: int) -> None:
        self.run_id = run_id
        self.expected = expected
        self.received = received
        super().__init__(
            f"secuencia inválida en el run {run_id}: se esperaba {expected} y llegó {received}"
        )


@runtime_checkable
class EventSinkPort(Protocol):
    """Destino de los eventos de un run."""

    async def emit(self, event: RunEvent) -> None:
        """Registra un evento.

        Debe rechazar con `EventSequenceError` cualquier evento cuya `sequence`
        no sea exactamente la siguiente del run.
        """
        ...

    async def read(self, run_id: str, *, after: int = 0) -> tuple[RunEvent, ...]:
        """Eventos posteriores a una posición conocida, para replay y reconexión."""
        ...

    async def last_sequence(self, run_id: str) -> int:
        """Última `sequence` registrada del run; 0 si no hay ninguna."""
        ...
