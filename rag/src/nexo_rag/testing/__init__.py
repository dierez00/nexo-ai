"""Dobles de prueba de RAG (`DIE-F0-024`, `DIE-F0-025`).

Sin red, sin PostgreSQL y sin pgvector. Aplican las mismas reglas de filtrado y
el mismo orden determinista que el repositorio real.
"""

from .embeddings import DIMENSION, MODEL_NAME, DeterministicEmbeddings
from .retriever import InMemoryChunkRepository, InMemoryRetriever, detect_injection

__all__ = [
    "DIMENSION",
    "MODEL_NAME",
    "DeterministicEmbeddings",
    "InMemoryChunkRepository",
    "InMemoryRetriever",
    "detect_injection",
]
