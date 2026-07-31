"""Montaje del corpus real en memoria, para pruebas y baselines.

Ingiere los manifests del repositorio contra un `InMemoryChunkRepository` y
devuelve un `HybridRetriever` listo. Es el mismo pipeline que correrá contra
PostgreSQL —mismo manifest, mismo chunking, mismos identificadores— con el
repositorio sustituido, que es exactamente la propiedad que `DIE-F0-030` pide
conservar.

Vive en `testing/` porque construye el índice completo en memoria en cada
llamada: es aceptable para decenas de fragmentos y no lo sería para el corpus
real.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nexo_contracts import Domain

from ..corpus import CorpusIngestion, IngestionReport, load_domain_manifest
from ..corpus.cli import MVP_DOMAINS, repository_root
from ..ports import EmbeddingsPort
from ..retrieval import HybridRetriever
from .embeddings import DeterministicEmbeddings
from .retriever import InMemoryChunkRepository

DEFAULT_NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


@dataclass
class LoadedCorpus:
    """Corpus indexado más lo necesario para construir un retriever por dominio."""

    repository: InMemoryChunkRepository
    reports: dict[Domain, IngestionReport]
    embeddings: EmbeddingsPort

    @property
    def corpus_versions(self) -> dict[Domain, str]:
        return {domain: report.result.corpus_version for domain, report in self.reports.items()}

    def retriever(self, domain: Domain, *, min_fused_score: float | None = None) -> HybridRetriever:
        """Retriever apuntando a la versión de corpus de ese dominio.

        El `corpus_version` viaja en cada citación, así que un retriever no
        puede servir a dos dominios con corpus versionados por separado sin
        mentir en la citación.
        """
        overrides = {} if min_fused_score is None else {"min_fused_score": min_fused_score}
        return HybridRetriever(
            repository=self.repository,
            embeddings=self.embeddings,
            corpus_version=self.corpus_versions[domain],
            **overrides,
        )


async def load_corpus(
    *,
    root: Path | None = None,
    domains: Sequence[Domain] = MVP_DOMAINS,
    embeddings: EmbeddingsPort | None = None,
    now: datetime = DEFAULT_NOW,
) -> LoadedCorpus:
    """Ingiere los manifests indicados y devuelve el corpus listo para consultar."""
    resolved_root = root or repository_root()
    repository = InMemoryChunkRepository()
    port = embeddings or DeterministicEmbeddings()
    ingestion = CorpusIngestion(repository=repository, embeddings=port, root=resolved_root, now=now)

    reports: dict[Domain, IngestionReport] = {}
    for domain in domains:
        manifest = load_domain_manifest(resolved_root, domain)
        reports[domain] = await ingestion.ingest(manifest)

    repository.store_vectors(ingestion.vectors())
    return LoadedCorpus(repository=repository, reports=reports, embeddings=port)
