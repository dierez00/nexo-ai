"""Contratos de RAG (§5.3).

Cubren el linaje completo `Source → Document → DocumentVersion → Chunk` y las
formas de consulta y respuesta. El filtro por institución, dominio, estado y
vigencia es parte del contrato de consulta, no una cortesía del retriever: un
resultado que no lo satisface no debe existir.
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import FrozenNexoModel, NexoModel
from .enums import CorpusStatus, Domain, IngestionOutcome, RetrievalMode, SourceStatus
from .facts import SourceCitation
from .ids import ChunkId, DocumentId, FragmentId, InstitutionId, SourceId
from .primitives import CalendarDate, CheckedValidityWindow, Score, Slug, UtcDatetime

Checksum = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]
"""Checksum de contenido con algoritmo explícito, para ingesta idempotente."""


class Source(NexoModel):
    """Fuente institucional registrada (§5.3).

    Los metadatos obligatorios son los que permiten auditar una respuesta: sin
    institución, responsable, licencia y vigencia, una fuente no puede activarse
    (`DIE-F2-022`).
    """

    source_id: SourceId
    title: str = Field(max_length=300)
    institution_id: InstitutionId
    domain: Domain
    origin_url: str | None = Field(default=None, max_length=1000)
    publisher: str = Field(max_length=200)
    owner: str = Field(max_length=200, description="Responsable interno de la fuente.")
    license: str = Field(max_length=200)
    status: SourceStatus = SourceStatus.DRAFT
    validity: CheckedValidityWindow
    verified_at: UtcDatetime | None = None
    is_synthetic: bool = Field(
        default=True,
        description="Marca el contenido sintético de demo frente al institucional autorizado.",
    )

    @model_validator(mode="after")
    def _active_sources_must_be_verified(self) -> Self:
        if self.status is SourceStatus.ACTIVE and self.verified_at is None:
            raise ValueError(
                f"la fuente {self.source_id!r} no puede estar activa sin verified_at: "
                f"el retrieval solo entrega evidencia verificada"
            )
        return self


class Document(NexoModel):
    """Archivo concreto asociado a una fuente."""

    document_id: DocumentId
    source_id: SourceId
    title: str = Field(max_length=300)
    media_type: str = Field(max_length=100)
    original_path: str = Field(
        max_length=500,
        description="Ruta al archivo original preservado; la ingesta nunca lo sobrescribe.",
    )


class DocumentVersion(NexoModel):
    """Versión inmutable de un documento.

    Un cambio de contenido crea una versión nueva; jamás se sobrescribe
    evidencia histórica (`DIE-F1-015`).
    """

    document_id: DocumentId
    version: str = Field(max_length=40)
    checksum: Checksum
    ingested_at: UtcDatetime
    supersedes: str | None = Field(default=None, max_length=40)
    is_active: bool = True


class Chunk(FrozenNexoModel):
    """Fragmento indexado y citable.

    `fragment_id` es la unidad que aparece en una citación; `char_start` y
    `char_end` permiten reconstruir el tramo exacto sobre el original.
    """

    chunk_id: ChunkId
    fragment_id: FragmentId
    document_id: DocumentId
    source_id: SourceId
    domain: Domain
    institution_id: InstitutionId
    document_version: str = Field(max_length=40)
    ordinal: int = Field(ge=0)
    heading: str | None = Field(default=None, max_length=300)
    text: str = Field(max_length=8000)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    checksum: Checksum
    validity: CheckedValidityWindow
    status: SourceStatus
    embedding_model: str | None = Field(default=None, max_length=120)
    embedding_dimension: int | None = Field(default=None, ge=1, le=8192)

    @model_validator(mode="after")
    def _offsets_are_coherent(self) -> Self:
        if self.char_end <= self.char_start:
            raise ValueError(
                f"offsets inválidos en {self.chunk_id!r}: char_end ({self.char_end}) debe ser "
                f"mayor que char_start ({self.char_start})"
            )
        return self


class CorpusVersion(NexoModel):
    """Instantánea versionada del corpus de un dominio (§5.3)."""

    corpus_version: str = Field(max_length=120)
    domain: Domain
    status: CorpusStatus
    created_at: UtcDatetime
    source_ids: Annotated[list[SourceId], Field(max_length=1000)] = Field(default_factory=list)
    chunk_count: int = Field(default=0, ge=0)
    supersedes: str | None = Field(default=None, max_length=120)


class RetrievalFilters(NexoModel):
    """Filtros obligatorios antes de devolver texto a un agente (`DIE-F1-022`)."""

    institution_id: InstitutionId
    status: Annotated[list[SourceStatus], Field(min_length=1, max_length=4)] = Field(
        default_factory=lambda: [SourceStatus.ACTIVE]
    )
    valid_at: CalendarDate
    allowed_source_ids: Annotated[list[SourceId], Field(max_length=200)] | None = Field(
        default=None,
        description="Si viene, restringe el retrieval a esta allowlist exacta.",
    )


class RetrievalQuery(NexoModel):
    """Consulta al retriever (§5.3)."""

    query: str = Field(min_length=1, max_length=2000)
    domain: Domain
    mini_rag: Slug | None = Field(
        default=None, description="Subíndice especializado; nulo usa el namespace general."
    )
    filters: RetrievalFilters
    top_k: int = Field(default=5, ge=1, le=50)
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    max_total_chars: int = Field(
        default=12000,
        ge=100,
        le=200_000,
        description="Presupuesto de contexto; el retriever trunca por resultado completo.",
    )


class RetrievalResult(NexoModel):
    """Un fragmento recuperado, con puntajes desglosados y su citación lista."""

    fragment_id: FragmentId
    source_id: SourceId
    title: str = Field(max_length=300)
    text: str = Field(max_length=8000)
    lexical_score: Score | None = None
    vector_score: Score | None = None
    fused_score: Score
    citation: SourceCitation
    injection_signals: Annotated[list[str], Field(max_length=20)] = Field(
        default_factory=list,
        description=(
            "Patrones de prompt injection detectados en el texto. Se registran como "
            "señal; el contenido nunca se obedece (`DIE-F1-026`)."
        ),
    )

    @model_validator(mode="after")
    def _citation_matches_fragment(self) -> Self:
        if self.citation.fragment_id != self.fragment_id:
            raise ValueError(
                f"la citación apunta a {self.citation.fragment_id!r} pero el resultado es "
                f"{self.fragment_id!r}"
            )
        if self.citation.source_id != self.source_id:
            raise ValueError(
                f"la citación apunta a la fuente {self.citation.source_id!r} pero el resultado "
                f"proviene de {self.source_id!r}"
            )
        return self


class RetrievalResponse(NexoModel):
    """Respuesta completa del retriever, siempre con `corpus_version` (`DIE-F1-024`)."""

    results: Annotated[list[RetrievalResult], Field(max_length=50)] = Field(default_factory=list)
    corpus_version: str = Field(max_length=120)
    filtered_count: int = Field(
        default=0,
        ge=0,
        description="Resultados descartados por institución, vigencia, estado o permiso.",
    )

    @model_validator(mode="after")
    def _results_are_ordered_and_unique(self) -> Self:
        """El orden es parte del contrato: la fusión debe ser estable ante empates."""
        seen: set[str] = set()
        previous: float | None = None
        for result in self.results:
            if result.fragment_id in seen:
                raise ValueError(f"fragment_id duplicado en la respuesta: {result.fragment_id!r}")
            seen.add(result.fragment_id)
            if previous is not None and result.fused_score > previous:
                raise ValueError(
                    "los resultados deben venir ordenados por fused_score descendente; "
                    f"{result.fragment_id!r} rompe el orden"
                )
            previous = result.fused_score
        return self


class IngestionResult(NexoModel):
    """Reporte de una corrida de ingesta (§5.3).

    Permite verificar idempotencia: reingerir sin cambios produce solo
    `unchanged` y no crea chunks nuevos (`DIE-F1-019`).
    """

    corpus_version: str = Field(max_length=120)
    domain: Domain
    outcomes: dict[IngestionOutcome, int] = Field(default_factory=dict)
    rejected_reasons: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    checksums: dict[str, Checksum] = Field(default_factory=dict)
    chunks_created: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _unchanged_runs_create_nothing(self) -> Self:
        created = self.outcomes.get(IngestionOutcome.CREATED, 0)
        superseded = self.outcomes.get(IngestionOutcome.SUPERSEDED, 0)
        if created == 0 and superseded == 0 and self.chunks_created > 0:
            raise ValueError(
                "una ingesta sin altas ni sustituciones no puede crear chunks: "
                "rompería la idempotencia de reingesta"
            )
        return self
