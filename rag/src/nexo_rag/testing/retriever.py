"""Retriever en memoria (`DIE-F0-025`).

Aplica **los mismos filtros lógicos** que aplicará el repositorio final sobre
PostgreSQL: institución, dominio, estado y vigencia se evalúan antes de puntuar,
no después. Esa es la única forma de que una prueba que pasa aquí signifique
algo cuando el retriever real la sustituya.

La fusión de puntajes es determinista y estable ante empates: mismo corpus y
misma consulta producen exactamente el mismo orden, siempre.
"""

from __future__ import annotations

import re

from nexo_contracts import (
    Chunk,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    SourceCitation,
    SourceStatus,
)

_TOKEN = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)

# Señales de prompt injection documental. Se registran como dato, nunca se
# obedecen: el contenido recuperado es información, no instrucciones
# (`DIE-F1-025`, `DIE-F1-026`).
_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instruction_override", re.compile(r"ignora (las |tus )?(instrucciones|reglas)", re.I)),
    ("role_hijack", re.compile(r"(actúa|actua) como (si fueras|un)", re.I)),
    ("tool_escalation", re.compile(r"(ejecuta|invoca|llama) (la )?(tool|herramienta)", re.I)),
    (
        "exfiltration",
        re.compile(r"(revela|muestra|envía) (el |la )?(prompt|api[_ ]?key|token)", re.I),
    ),
)

# Peso de la señal léxica en la fusión. Fijo y explícito para que el resultado
# sea reproducible; el reranking ponderado real se decide en Fase 1 (`DIE-F1-021`).
LEXICAL_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN.finditer(text)}


def detect_injection(text: str) -> list[str]:
    """Nombres de las señales de injection presentes en el texto."""
    return [name for name, pattern in _INJECTION_PATTERNS if pattern.search(text)]


class InMemoryRetriever:
    """Implementación de `RetrieverPort` sobre una lista de chunks en memoria."""

    def __init__(self, chunks: list[Chunk] | None = None, *, corpus_version: str = "") -> None:
        self._chunks: list[Chunk] = list(chunks or [])
        self._corpus_version = corpus_version

    def add(self, *chunks: Chunk) -> None:
        self._chunks.extend(chunks)

    def _is_authorized(self, chunk: Chunk, query: RetrievalQuery) -> bool:
        """Filtros obligatorios. Un chunk que falle aquí no se puntúa siquiera."""
        filters = query.filters
        if chunk.institution_id != filters.institution_id:
            return False
        if chunk.domain is not query.domain:
            return False
        if chunk.status not in filters.status:
            return False
        if not chunk.validity.covers(filters.valid_at):
            return False
        allowlist = filters.allowed_source_ids
        return allowlist is None or chunk.source_id in allowlist

    def _score(self, chunk: Chunk, query_tokens: set[str]) -> tuple[float, float, float]:
        chunk_tokens = _tokens(chunk.text) | _tokens(chunk.heading or "")
        if query_tokens and chunk_tokens:
            overlap = len(query_tokens & chunk_tokens)
            lexical = overlap / len(query_tokens)
        else:
            lexical = 0.0

        # Sustituto determinista de la similitud vectorial: proporción del
        # vocabulario del fragmento cubierta por la consulta. No es semántico y
        # no pretende serlo (ver `DeterministicEmbeddings`).
        vector = len(query_tokens & chunk_tokens) / len(chunk_tokens) if chunk_tokens else 0.0
        fused = min(1.0, LEXICAL_WEIGHT * lexical + VECTOR_WEIGHT * vector)
        return lexical, vector, fused

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        query_tokens = _tokens(query.query)
        authorized: list[Chunk] = []
        filtered = 0
        for chunk in self._chunks:
            if self._is_authorized(chunk, query):
                authorized.append(chunk)
            else:
                filtered += 1

        scored: list[tuple[float, float, float, Chunk]] = []
        for chunk in authorized:
            lexical, vector, fused = self._score(chunk, query_tokens)
            if fused <= 0.0:
                filtered += 1
                continue
            scored.append((lexical, vector, fused, chunk))

        # Desempate por `fragment_id`: sin él, dos fragmentos con el mismo
        # puntaje podrían alternar de orden entre ejecuciones.
        scored.sort(key=lambda item: (-item[2], item[3].fragment_id))

        results: list[RetrievalResult] = []
        used_chars = 0
        for lexical, vector, fused, chunk in scored[: query.top_k]:
            if used_chars + len(chunk.text) > query.max_total_chars:
                filtered += 1
                continue
            used_chars += len(chunk.text)
            results.append(
                RetrievalResult(
                    fragment_id=chunk.fragment_id,
                    source_id=chunk.source_id,
                    title=chunk.heading or chunk.document_id,
                    text=chunk.text,
                    lexical_score=lexical,
                    vector_score=vector,
                    fused_score=fused,
                    citation=SourceCitation(
                        source_id=chunk.source_id,
                        fragment_id=chunk.fragment_id,
                        corpus_version=self._corpus_version,
                        source_version=chunk.document_version,
                        valid_from=chunk.validity.valid_from,
                        valid_to=chunk.validity.valid_to,
                        is_active=chunk.status is SourceStatus.ACTIVE,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                    ),
                    injection_signals=detect_injection(chunk.text),
                )
            )

        return RetrievalResponse(
            results=results,
            corpus_version=self._corpus_version,
            filtered_count=filtered,
        )


class InMemoryChunkRepository:
    """Repositorio de chunks idempotente por checksum (`DIE-F1-019`).

    Guarda vectores junto a los fragmentos, en un mapa aparte, porque así los
    guardará el repositorio real: el `Chunk` es el contrato publicado y no
    transporta 256 flotantes.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, Chunk] = {}
        self._vectors: dict[str, list[float]] = {}

    async def upsert(self, chunks: list[Chunk]) -> int:
        created = 0
        for chunk in chunks:
            existing = self._by_id.get(chunk.chunk_id)
            if existing is not None and existing.checksum == chunk.checksum:
                continue  # sin cambios: reingerir no duplica
            if existing is None:
                created += 1
            self._by_id[chunk.chunk_id] = chunk
        return created

    async def count(self, *, corpus_version: str) -> int:
        del corpus_version  # el doble mantiene un único corpus en memoria
        return len(self._by_id)

    async def get(self, chunk_id: str) -> Chunk | None:
        return self._by_id.get(chunk_id)

    async def candidates(self, *, domain: str, institution_id: str) -> tuple[Chunk, ...]:
        """Acota por dominio e institución antes de que nadie puntúe nada.

        El orden es estable por `chunk_id` para que dos corridas produzcan la
        misma lista de candidatos y, por tanto, el mismo BM25: el IDF depende de
        la colección, así que un orden inestable movería los puntajes.
        """
        return tuple(
            self._by_id[key]
            for key in sorted(self._by_id)
            if self._by_id[key].domain.value == domain
            and self._by_id[key].institution_id == institution_id
        )

    async def vector_of(self, chunk_id: str) -> list[float] | None:
        return self._vectors.get(chunk_id)

    def store_vectors(self, vectors: dict[str, list[float]]) -> None:
        """Registra los vectores que produjo la ingesta."""
        self._vectors.update(vectors)

    def all_chunks(self) -> list[Chunk]:
        return list(self._by_id.values())
