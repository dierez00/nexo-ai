"""Embeddings deterministas para pruebas (`DIE-F0-024`).

**Solo sirven para pruebas.** No tienen ninguna propiedad semántica: dos textos
con el mismo significado no quedan cerca en este espacio. Sustituyen a un
adapter real únicamente para verificar que el pipeline registra modelo,
dimensión y versión, y que la ingesta es idempotente.

Usar esto para medir recall o precisión produciría un número sin significado.
"""

from __future__ import annotations

import hashlib
import math

MODEL_NAME = "fake-embeddings-v1"
DIMENSION = 64


class DeterministicEmbeddings:
    """Vectores derivados del hash del texto: mismo texto, mismo vector, siempre."""

    def __init__(self, *, dimension: int = DIMENSION) -> None:
        if dimension < 1 or dimension > 4096:
            raise ValueError("la dimensión debe estar entre 1 y 4096")
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return MODEL_NAME

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # El digest tiene 32 bytes; se repite hasta cubrir la dimensión pedida.
        raw = [digest[index % len(digest)] / 255.0 for index in range(self._dimension)]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        return [value / norm for value in raw]
