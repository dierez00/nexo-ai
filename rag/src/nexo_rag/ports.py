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

    @property
    def is_semantic(self) -> bool:
        """Si los vectores tienen significado semántico real.

        Los dobles de prueba derivan vectores de un hash y deben devolver
        `False`. No es una etiqueta informativa: el retriever híbrido la
        consulta y degrada a búsqueda léxica cuando es falsa, porque una mitad
        vectorial sin semántica no aporta ruido inofensivo —pesa 0.6 en la
        fusión y **ahoga** la mitad que sí discrimina.

        Sin esta señal, el perfil offline mediría un retriever que ordena por
        azar y lo reportaría como si fuera el comportamiento real.
        """
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

    async def get(self, chunk_id: str) -> Chunk | None:
        """Un fragmento por su identificador, o `None` si no está indexado.

        La ingesta lo usa para decidir si una versión ya está indexada sin tener
        que leer el corpus entero (`DIE-F1-014`).
        """
        ...

    async def candidates(self, *, domain: str, institution_id: str) -> tuple[Chunk, ...]:
        """Fragmentos de un dominio e institución, para que el retriever puntúe.

        El acotado por dominio e institución ocurre **en el repositorio**, no
        después: en PostgreSQL será un `WHERE` con índice, y en memoria un
        filtro. Traer el corpus completo a la aplicación para descartarlo allí
        no escalaría y, peor, dejaría texto de otra institución al alcance de un
        error de programación (`DIE-F1-022`).
        """
        ...

    async def vector_of(self, chunk_id: str) -> list[float] | None:
        """Vector del fragmento, o `None` si se indexó sin embedding.

        Se consulta aparte del `Chunk` porque un vector no cabe razonablemente
        dentro de un contrato publicado ni dentro de un fixture legible.
        """
        ...
