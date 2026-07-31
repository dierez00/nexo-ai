"""Reloj y fábrica de identificadores inyectables (`DIE-F0-028`).

Sin estos dos puertos no hay snapshots reproducibles: cada ejecución produciría
timestamps e IDs distintos y ninguna prueba podría comparar bytes. Ningún módulo
de Diego llama a `datetime.now()` ni a `uuid4()` directamente.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Fuente de tiempo del sistema. Siempre devuelve un instante en UTC."""

    def now(self) -> datetime:
        """Instante actual, con zona horaria UTC."""
        ...

    def monotonic_ms(self) -> int:
        """Milisegundos monotónicos para medir duraciones y deadlines.

        Se separa de `now()` a propósito: medir una duración con el reloj de
        pared produce valores negativos si el reloj se ajusta.
        """
        ...


@runtime_checkable
class IdFactory(Protocol):
    """Fábrica de identificadores opacos con prefijo."""

    def new_id(self, prefix: str) -> str:
        """Identificador nuevo con el prefijo indicado, por ejemplo `run_`."""
        ...
