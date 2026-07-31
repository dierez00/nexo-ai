"""Reloj y fábrica de IDs controlables (`DIE-F0-028`).

Congelar ambos es lo que permite comparar dos ejecuciones byte a byte. Con un
reloj real y UUIDs aleatorios, cualquier snapshot difiere siempre y las pruebas
de reproducibilidad no significan nada.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from nexo_contracts.ids import ID_PREFIXES

DEFAULT_EPOCH = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


class FrozenClock:
    """Reloj determinista que solo avanza cuando se le pide.

    `advance()` existe para simular deadlines y medir duraciones sin dormir el
    proceso: una prueba de timeout no debe tardar lo que tarda el timeout.
    """

    def __init__(self, start: datetime = DEFAULT_EPOCH, *, step_ms: int = 0) -> None:
        if start.tzinfo is None:
            raise ValueError("el reloj congelado exige un instante con zona horaria")
        self._now = start.astimezone(UTC)
        self._monotonic_ms = 0
        self._step_ms = step_ms

    def now(self) -> datetime:
        current = self._now
        if self._step_ms:
            self.advance(self._step_ms)
        return current

    def monotonic_ms(self) -> int:
        return self._monotonic_ms

    def advance(self, milliseconds: int) -> None:
        """Avanza el reloj de pared y el monotónico en la misma cantidad."""
        if milliseconds < 0:
            raise ValueError("el reloj no retrocede")
        self._now += timedelta(milliseconds=milliseconds)
        self._monotonic_ms += milliseconds


class SequentialIdFactory:
    """Fábrica de IDs predecibles: `run_000001`, `evt_000002`…

    Los contadores son por prefijo para que añadir un evento no desplace los
    identificadores de las tools y viceversa; así un cambio en una parte del
    grafo no invalida los snapshots de otra.
    """

    def __init__(self, *, width: int = 6) -> None:
        self._counters: dict[str, int] = {}
        self._width = width

    def new_id(self, prefix: str) -> str:
        if prefix not in ID_PREFIXES:
            raise KeyError(
                f"prefijo de ID no registrado: {prefix!r}. Los prefijos válidos son "
                f"{sorted(ID_PREFIXES)}"
            )
        nxt = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = nxt
        return f"{prefix}_{nxt:0{self._width}d}"

    def reset(self) -> None:
        self._counters.clear()
