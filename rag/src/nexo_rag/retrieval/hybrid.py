"""Retriever híbrido: léxico + vectorial detrás de un repositorio (F1.3).

Implementa `RetrieverPort` combinando BM25 (`DIE-F1-020`) con similitud coseno
sobre embeddings, y aplica en este orden, que no es negociable:

    filtrar → puntuar → fusionar → desempatar → recortar por presupuesto

**Filtrar antes de puntuar** (`DIE-F1-022`) es la diferencia entre un guardrail
y una sugerencia: un fragmento de otra institución, de otro dominio, vencido o
sustituido no compite, ni siquiera con puntaje perfecto. Filtrar después
significaría que un error de ordenación puede filtrar texto no autorizado.

**La fusión es determinista y estable ante empates** (`DIE-F1-021`). El
desempate es por `fragment_id`, que es estable entre corridas. Sin él, dos
fragmentos con idéntico puntaje alternarían de orden y ningún baseline sería
comparable entre commits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from nexo_contracts import (
    Chunk,
    RetrievalMode,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    SourceCitation,
    SourceStatus,
)

from ..ports import ChunkRepositoryPort, EmbeddingsPort
from ..safety import detect_injection
from .lexical import BM25Index

# Peso de cada mitad en la fusión. El léxico pesa menos porque el corpus
# institucional repite vocabulario administrativo («solicitud», «trámite»,
# «vigencia») en casi todo fragmento, y eso infla BM25 sin discriminar. Ambos
# valores son configurables por consulta, pero su default es parte del
# comportamiento reproducible del baseline.
LEXICAL_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6

# Suelo por debajo del cual un fragmento ni siquiera se devuelve. Es
# deliberadamente **bajo**: su función es recortar la cola de ruido, no decidir
# si la evidencia basta.
#
# Se intentó lo contrario —un umbral alto que filtrara las consultas fuera de
# alcance— y los datos lo desmienten: sobre este corpus, la consulta fuera de
# alcance «cómo tramito mi pasaporte» puntúa 0.308 y la consulta legítima «qué
# permisos necesito para abrir una taquería» puntúa 0.280. Se **solapan**, así
# que ningún umbral absoluto las separa, y subirlo solo descarta evidencia buena.
#
# La separación correcta es de responsabilidades: el retriever **ordena**, y
# `retrieval.sufficiency.assess` decide si lo recuperado sostiene un claim
# crítico (`DIE-F1-027`). Un solo número no puede hacer las dos cosas.
MIN_FUSED_SCORE = 0.08
MIN_LEXICAL_SCORE = 0.08


def cosine(left: list[float], right: list[float]) -> float:
    """Coseno acotado a `[0, 1]`.

    Los puntajes de los contratos viven en `[0, 1]`, así que la parte negativa
    —vectores en direcciones opuestas— se colapsa a cero. Para relevancia eso es
    correcto: «opuesto» y «no relacionado» son igual de irrelevantes.
    """
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_left * norm_right)))


@dataclass(frozen=True)
class _Scored:
    chunk: Chunk
    lexical: float
    vector: float
    fused: float


@dataclass
class HybridRetriever:
    """Recuperación híbrida sobre `ChunkRepositoryPort` y `EmbeddingsPort`.

    No conoce PostgreSQL ni pgvector: el repositorio decide cómo trae los
    candidatos de un dominio e institución, y este objeto decide cuáles de esos
    candidatos son evidencia entregable.
    """

    repository: ChunkRepositoryPort
    embeddings: EmbeddingsPort
    corpus_version: str
    lexical_weight: float = LEXICAL_WEIGHT
    vector_weight: float = VECTOR_WEIGHT
    min_fused_score: float = MIN_FUSED_SCORE
    min_lexical_score: float = MIN_LEXICAL_SCORE

    def _is_authorized(self, chunk: Chunk, query: RetrievalQuery) -> bool:
        """Filtros obligatorios. Un fragmento que falle aquí no llega a puntuarse."""
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

    def _effective_mode(self, requested: RetrievalMode) -> RetrievalMode:
        """Modo realmente aplicable con los embeddings inyectados.

        Un puerto de embeddings sin semántica (`is_semantic == False`) degrada
        `hybrid` a `lexical`. Es deliberado y no silencioso: la alternativa
        —fusionar de todas formas— produce un orden dominado por ruido, porque
        la mitad vectorial pesa 0.6 y no discrimina nada. Medir eso y llamarlo
        «el retriever híbrido» sería reportar un número falso (TD-02).
        """
        if requested is RetrievalMode.LEXICAL:
            return RetrievalMode.LEXICAL
        if getattr(self.embeddings, "is_semantic", True):
            return requested
        if requested is RetrievalMode.VECTOR:
            raise ValueError(
                "se pidió recuperación puramente vectorial con embeddings sin semántica; "
                "no hay forma honesta de servir esa consulta"
            )
        return RetrievalMode.LEXICAL

    async def _vector_scores(
        self, query: RetrievalQuery, candidates: list[Chunk]
    ) -> dict[str, float]:
        """Similitud coseno contra el vector de la consulta.

        Si un fragmento se indexó sin embedding —corpus a medio migrar, modelo
        cambiado— su componente vectorial es cero y solo compite por léxico. Es
        preferible a excluirlo: la evidencia sigue siendo válida aunque su
        vector falte.
        """
        if self._effective_mode(query.retrieval_mode) is RetrievalMode.LEXICAL:
            return {}
        embedded = await self.embeddings.embed([query.query])
        if not embedded:
            return {}
        needle = embedded[0]

        scores: dict[str, float] = {}
        for chunk in candidates:
            vector = await self.repository.vector_of(chunk.chunk_id)
            if vector is None:
                continue
            scores[chunk.chunk_id] = cosine(needle, vector)
        return scores

    def _lexical_scores(self, query: RetrievalQuery, candidates: list[Chunk]) -> dict[str, float]:
        if self._effective_mode(query.retrieval_mode) is RetrievalMode.VECTOR:
            return {}
        index = BM25Index.from_texts(
            {chunk.chunk_id: f"{chunk.heading or ''}\n{chunk.text}" for chunk in candidates}
        )
        return index.score(query.query)

    def _fuse(self, lexical: float, vector: float, mode: RetrievalMode) -> float:
        """Combina ambas mitades respetando el modo pedido.

        En modo `lexical` o `vector` no se reescala la mitad presente: pedir
        solo léxico debe devolver el puntaje léxico, no el 40% de él.
        """
        if mode is RetrievalMode.LEXICAL:
            return lexical
        if mode is RetrievalMode.VECTOR:
            return vector
        return min(1.0, self.lexical_weight * lexical + self.vector_weight * vector)

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        raw = await self.repository.candidates(
            domain=query.domain.value, institution_id=query.filters.institution_id
        )
        filtered = 0
        candidates: list[Chunk] = []
        for chunk in raw:
            if self._is_authorized(chunk, query):
                candidates.append(chunk)
            else:
                filtered += 1

        mode = self._effective_mode(query.retrieval_mode)
        lexical = self._lexical_scores(query, candidates)
        vector = await self._vector_scores(query, candidates)

        scored: list[_Scored] = []
        for chunk in candidates:
            lexical_score = lexical.get(chunk.chunk_id, 0.0)
            vector_score = vector.get(chunk.chunk_id, 0.0)
            fused = self._fuse(lexical_score, vector_score, mode)
            floor = (
                self.min_lexical_score if mode is RetrievalMode.LEXICAL else self.min_fused_score
            )
            if fused < floor:
                filtered += 1
                continue
            scored.append(
                _Scored(chunk=chunk, lexical=lexical_score, vector=vector_score, fused=fused)
            )

        # Desempate por `fragment_id`: estable entre corridas y entre máquinas.
        scored.sort(key=lambda item: (-item.fused, item.chunk.fragment_id))

        results: list[RetrievalResult] = []
        used_chars = 0
        for item in scored[: query.top_k]:
            # `DIE-F1-023`: el presupuesto de contexto se respeta por resultado
            # completo. Truncar un fragmento a la mitad produciría una citación
            # que no dice lo que su texto original decía.
            if used_chars + len(item.chunk.text) > query.max_total_chars:
                filtered += 1
                continue
            used_chars += len(item.chunk.text)
            results.append(self._to_result(item))

        return RetrievalResponse(
            results=results,
            corpus_version=self.corpus_version,
            filtered_count=filtered,
        )

    def _to_result(self, item: _Scored) -> RetrievalResult:
        chunk = item.chunk
        return RetrievalResult(
            fragment_id=chunk.fragment_id,
            source_id=chunk.source_id,
            title=chunk.heading or chunk.document_id,
            text=chunk.text,
            lexical_score=item.lexical,
            vector_score=item.vector,
            fused_score=item.fused,
            # `DIE-F1-024`: la citación viaja completa y con `corpus_version`.
            # Un resultado sin ella no puede sostener un claim crítico.
            citation=SourceCitation(
                source_id=chunk.source_id,
                fragment_id=chunk.fragment_id,
                corpus_version=self.corpus_version,
                source_version=chunk.document_version,
                valid_from=chunk.validity.valid_from,
                valid_to=chunk.validity.valid_to,
                is_active=chunk.status is SourceStatus.ACTIVE,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
            ),
            injection_signals=detect_injection(chunk.text),
        )
