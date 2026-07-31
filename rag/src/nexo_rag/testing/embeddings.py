"""Embeddings deterministas para pruebas (`DIE-F0-024`).

**Solo sirven para pruebas.** No tienen ninguna propiedad semántica: dos textos
con el mismo significado no quedan cerca en este espacio. Sustituyen a un
adapter real únicamente para verificar que el pipeline registra modelo,
dimensión y versión, y que la ingesta es idempotente.

Usar esto para medir recall o precisión produciría un número sin significado; el
baseline de calidad exige `nexo_rag.embeddings.StaticSemanticEmbeddings` (F1.3).

**Los vectores están centrados en cero.** No es cosmética: derivados de bytes de
un hash, todos los componentes serían positivos y el coseno entre dos textos sin
relación alguna daría ~0.8. Con el retriever híbrido eso es activamente dañino,
porque la mitad vectorial —que no significa nada— domina la fusión y ahoga la
mitad léxica, que sí. Centrados, el coseno de dos textos no relacionados ronda
cero: el componente vectorial aporta ruido despreciable en vez de una señal
falsa, y lo que se observa en la suite offline es el comportamiento léxico real.
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

    @property
    def is_semantic(self) -> bool:
        """Falso, y es lo más importante que declara esta clase.

        El retriever híbrido lo consulta para degradar a búsqueda léxica. Sin
        eso, la suite offline mediría un orden dominado por ruido.
        """
        return False

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        # Se extiende el hash hasta cubrir la dimensión pedida: 32 bytes por
        # bloque, con el índice del bloque dentro del propio hash para que dos
        # bloques del mismo texto no sean idénticos.
        raw: list[float] = []
        block = 0
        while len(raw) < self._dimension:
            digest = hashlib.sha256(f"{block}\x1f{text}".encode()).digest()
            raw.extend(byte / 255.0 for byte in digest)
            block += 1
        raw = raw[: self._dimension]

        # Centrado: sin él, todos los componentes serían positivos y el coseno
        # entre textos sin relación daría ~0.8 (ver el docstring del módulo).
        mean = sum(raw) / len(raw)
        centered = [value - mean for value in raw]
        norm = math.sqrt(sum(value * value for value in centered)) or 1.0
        return [value / norm for value in centered]
