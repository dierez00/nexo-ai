"""Ingesta y recuperación de evidencia institucional de Nexo IA.

En Fase 0 el paquete publica únicamente sus **puertos** y los dobles en memoria
que los implementan. La ingesta real, el chunking, los embeddings de proveedor y
la búsqueda híbrida sobre PostgreSQL son trabajo de Fase 1 (F1.2 y F1.3).
"""

from .ports import ChunkRepositoryPort, EmbeddingsPort, RetrieverPort

__all__ = ["ChunkRepositoryPort", "EmbeddingsPort", "RetrieverPort"]
