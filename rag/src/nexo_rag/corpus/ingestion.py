"""Ingesta de corpus: verificar, fragmentar, vectorizar e indexar (F1.2).

El pipeline es deliberadamente aburrido y verificable:

    manifest → checksum → ¿cambió? → fragmentar → vectorizar → upsert

Las decisiones que importan están en los `¿?`:

- **Si el checksum coincide, no se hace nada** (`DIE-F1-014`). Reingerir un
  corpus intacto produce cero chunks nuevos, cero embeddings y cero escrituras.
- **Si el contenido cambió, se crea una versión nueva**; jamás se sobrescribe la
  anterior (`DIE-F1-015`). El corpus es evidencia, y la evidencia histórica es
  lo que permite explicar una respuesta emitida hace seis meses.
- **Las fuentes vencidas y sustituidas se ingieren igual**, con su estado real
  (`DIE-F1-016`). Excluirlas del índice las haría invisibles; lo que debe pasar
  es que el retriever las filtre y que esa exclusión sea observable.

La ingesta no conoce PostgreSQL: escribe contra `ChunkRepositoryPort` y
vectoriza contra `EmbeddingsPort`. Sustituir el repositorio en memoria por
pgvector no cambia una línea de este módulo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from nexo_contracts import (
    Chunk,
    CorpusStatus,
    CorpusVersion,
    Document,
    DocumentVersion,
    IngestionOutcome,
    IngestionResult,
    Source,
    SourceStatus,
)
from nexo_contracts.primitives import UtcDatetime

from ..ports import ChunkRepositoryPort, EmbeddingsPort
from .checksums import ChecksumMismatchError, checksum_of_text
from .chunking import chunk_document
from .ids import chunk_id, fragment_id
from .manifest import DocumentEntry, SourceEntry, SourceManifest


@dataclass
class IngestionReport:
    """Resultado de una corrida, más el linaje que el contrato no transporta."""

    result: IngestionResult
    sources: list[Source] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)
    versions: list[DocumentVersion] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    corpus: CorpusVersion | None = None

    @property
    def created(self) -> int:
        return self.result.outcomes.get(IngestionOutcome.CREATED, 0)

    @property
    def unchanged(self) -> int:
        return self.result.outcomes.get(IngestionOutcome.UNCHANGED, 0)


@dataclass
class CorpusIngestion:
    """Servicio de ingesta de un dominio.

    `strict_checksums` distingue dos usos legítimos: en la suite y en CI un
    archivo que no coincide con su manifest debe detener la ingesta, mientras
    que al redactar corpus conviene poder regenerar los checksums. Nunca se
    ignora en silencio: o falla, o se registra como rechazo.
    """

    repository: ChunkRepositoryPort
    embeddings: EmbeddingsPort
    root: Path
    now: UtcDatetime
    strict_checksums: bool = True
    _vectors: dict[str, list[float]] = field(default_factory=dict, init=False)

    async def ingest(self, manifest: SourceManifest) -> IngestionReport:
        """Ingiere el manifest completo y devuelve el reporte de la corrida."""
        report = IngestionReport(
            result=IngestionResult(
                corpus_version=manifest.corpus_version,
                domain=manifest.domain,
            )
        )
        outcomes: dict[IngestionOutcome, int] = {}
        checksums: dict[str, str] = {}
        rejected: list[str] = []
        pending: list[Chunk] = []

        for source in manifest.sources:
            report.sources.append(source.to_contract(manifest.domain))
            for entry in source.documents:
                outcome, chunks = await self._ingest_document(
                    manifest=manifest,
                    source=source,
                    entry=entry,
                    report=report,
                    rejected=rejected,
                    checksums=checksums,
                )
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
                pending.extend(chunks)

        created = await self._index(pending)
        report.chunks = pending
        report.result = IngestionResult(
            corpus_version=manifest.corpus_version,
            domain=manifest.domain,
            outcomes=outcomes,
            rejected_reasons=rejected,
            checksums=checksums,
            chunks_created=created,
        )
        report.corpus = CorpusVersion(
            corpus_version=manifest.corpus_version,
            domain=manifest.domain,
            status=CorpusStatus.ACTIVE,
            created_at=self.now,
            source_ids=[source.source_id for source in manifest.sources],
            chunk_count=await self.repository.count(corpus_version=manifest.corpus_version),
        )
        return report

    # -- un documento -----------------------------------------------------

    async def _ingest_document(
        self,
        *,
        manifest: SourceManifest,
        source: SourceEntry,
        entry: DocumentEntry,
        report: IngestionReport,
        rejected: list[str],
        checksums: dict[str, str],
    ) -> tuple[IngestionOutcome, list[Chunk]]:
        path = self.root / entry.path
        if not path.exists():
            rejected.append(f"{entry.document_id}: el archivo {entry.path} no existe")
            return IngestionOutcome.REJECTED, []

        text = path.read_text(encoding="utf-8")
        actual = checksum_of_text(text)
        checksums[entry.document_id] = actual

        if actual != entry.checksum:
            if self.strict_checksums:
                raise ChecksumMismatchError(entry.path, entry.checksum, actual)
            rejected.append(
                f"{entry.document_id}: checksum declarado {entry.checksum} ≠ real {actual}"
            )
            return IngestionOutcome.REJECTED, []

        # `DIE-F1-014`: sin cambios, no se toca el índice. Es la condición que
        # hace idempotente una reingesta completa.
        if await self._already_indexed(source, entry, actual):
            return IngestionOutcome.UNCHANGED, []

        try:
            fragments = chunk_document(text, media_type=entry.media_type)
        except ValueError as exc:
            rejected.append(f"{entry.document_id}: {exc}")
            return IngestionOutcome.REJECTED, []

        report.documents.append(source.document_contract(entry))
        report.versions.append(
            DocumentVersion(
                document_id=entry.document_id,
                version=entry.version,
                checksum=actual,
                ingested_at=self.now,
                supersedes=entry.supersedes,
                is_active=source.status is SourceStatus.ACTIVE,
            )
        )

        vectors = await self.embeddings.embed([fragment.text for fragment in fragments])
        # Ocurrencia de cada encabezado dentro del documento: desempata las
        # secciones que se llaman igual («Vigencia», «Requisitos») sin recurrir
        # al ordinal, que es justo lo que el `fragment_id` no debe depender.
        occurrences: dict[str | None, int] = {}
        headings: list[int] = []
        for fragment in fragments:
            index = occurrences.get(fragment.heading, 0)
            occurrences[fragment.heading] = index + 1
            headings.append(index)

        chunks = [
            Chunk(
                chunk_id=chunk_id(source.source_id, entry.document_id, entry.version, f.ordinal),
                fragment_id=fragment_id(
                    source.source_id, entry.document_id, entry.version, f.heading, occurrence
                ),
                document_id=entry.document_id,
                source_id=source.source_id,
                domain=manifest.domain,
                institution_id=source.institution_id,
                document_version=entry.version,
                ordinal=f.ordinal,
                heading=f.heading,
                text=f.text,
                char_start=f.char_start,
                char_end=f.char_end,
                checksum=checksum_of_text(f.text),
                validity=source.validity,
                status=source.status,
                embedding_model=self.embeddings.model_name,
                embedding_dimension=self.embeddings.dimension,
            )
            for f, occurrence in zip(fragments, headings, strict=True)
        ]
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._vectors[chunk.chunk_id] = vector

        outcome = IngestionOutcome.SUPERSEDED if entry.supersedes else IngestionOutcome.CREATED
        return outcome, chunks

    async def _already_indexed(
        self, source: SourceEntry, entry: DocumentEntry, checksum: str
    ) -> bool:
        """¿Está esta versión exacta ya en el índice, con el mismo contenido?"""
        existing = await self.repository.get(
            chunk_id(source.source_id, entry.document_id, entry.version, 0)
        )
        return (
            existing is not None
            and existing.document_version == entry.version
            and (checksum_of_text(existing.text) == existing.checksum)
        )

    async def _index(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        return await self.repository.upsert(chunks)

    def vectors(self) -> dict[str, list[float]]:
        """Vectores calculados en la última corrida, por `chunk_id`.

        Viven aquí y no en `Chunk` porque un vector de 256 dimensiones dentro
        del contrato lo haría ilegible y multiplicaría por diez el tamaño de
        cualquier fixture. El repositorio real los almacenará en su columna
        `vector`; el doble en memoria los recibe por separado.
        """
        return dict(self._vectors)
