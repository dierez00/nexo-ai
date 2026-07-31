"""Reloj y fábrica de IDs de producción para el grafo real.

Los dobles de `nexo_orchestration.testing` congelan tiempo e IDs para comparar
snapshots byte a byte. En producción el grafo necesita tiempo real e IDs
opacos únicos, respetando la misma interfaz (`Clock`, `IdFactory`).
"""

from __future__ import annotations

import base64
import secrets
import time
from datetime import UTC, datetime

from nexo_contracts.ids import ID_PREFIXES


class SystemClock:
    """`Clock` de pared en UTC más un reloj monotónico para medir duraciones."""

    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic_ms(self) -> int:
        return time.monotonic_ns() // 1_000_000


class UuidIdFactory:
    """`IdFactory` opaca: `<prefijo>_<cuerpo base32>`.

    Se usa base32 (letras + dígitos 2-7) en vez de hex a propósito: el cuerpo
    de un ID no puede contener una secuencia de 10+ dígitos decimales
    (`nexo_contracts.ids` la rechaza como posible PII), y una cadena hex la
    produciría con frecuencia inaceptable.
    """

    def new_id(self, prefix: str) -> str:
        if prefix not in ID_PREFIXES:
            raise KeyError(
                f"prefijo de ID no registrado: {prefix!r}. Válidos: {sorted(ID_PREFIXES)}"
            )
        body = base64.b32encode(secrets.token_bytes(16)).decode("ascii").rstrip("=").lower()
        return f"{prefix}_{body}"
