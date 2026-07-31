"""Puertos de recuperación y embeddings (`DIE-F0-021`).

`rag` expone contratos, no detalles de pgvector. El repositorio real (PostgreSQL
FTS + pgvector, responsabilidad compartida con Daher) y el doble en memoria
implementan este mismo protocolo, y las pruebas que los ejercen son las mismas.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nexo_contracts import Chunk, RetrievalQuery, RetrievalResponse


@runtime_checkable
class RetrieverPort(Protocol):
    """Recuperación de evidencia vigente y autorizada.

    Los filtros de institución, dominio, estado y vigencia se aplican **antes**
    de devolver texto: un fragmento que no los satisface no debe llegar nunca a
    un agente, ni siquiera con puntaje alto (`DIE-F1-022`).
    """

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        """Fragmentos ordenados por puntaje fusionado descendente."""
        ...


@runtime_checkable
class EmbeddingsPort(Protocol):
    """Generación de vectores para búsqueda semántica."""

    @property
    def model_name(self) -> str:
        """Nombre del modelo, registrado junto a cada chunk indexado."""
        ...

    @property
    def dimension(self) -> int:
        """Dimensión de los vectores producidos."""
        ...

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Vectores en el mismo orden que los textos recibidos."""
        ...


@runtime_checkable
class ChunkRepositoryPort(Protocol):
    """Almacenamiento de fragmentos indexados.

    Se separa del retriever porque la ingesta y la consulta tienen ciclos de vida
    distintos: una reingesta idempotente escribe, un run solo lee.
    """

    async def upsert(self, chunks: list[Chunk]) -> int:
        """Inserta o reemplaza fragmentos y devuelve cuántos se crearon.

        Debe ser idempotente por `checksum`: reingerir contenido sin cambios no
        crea fragmentos nuevos (`DIE-F1-019`).
        """
        ...

    async def count(self, *, corpus_version: str) -> int:
        """Fragmentos registrados para una versión de corpus."""
        ...
