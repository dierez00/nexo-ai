"""Snapshot global, lineage y diff reproducible del corpus Core (`DIE-F2-019`–`023`)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from nexo_contracts import Domain, NexoModel

if TYPE_CHECKING:
    from ..testing.corpus import LoadedCorpus


class LineageEntry(NexoModel):
    domain: Domain
    source_id: str
    document_id: str
    document_version: str
    chunk_id: str
    fragment_id: str
    chunk_checksum: str
    embedding_model: str
    embedding_dimension: int


class CorpusGlobalSnapshot(NexoModel):
    version: str = Field(max_length=120)
    generated_at: str
    corpus_versions: dict[Domain, str]
    chunk_counts: dict[Domain, int]
    lineage: Annotated[list[LineageEntry], Field(max_length=20_000)]
    digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class CorpusDiff(NexoModel):
    previous_version: str
    current_version: str
    added_chunks: Annotated[list[str], Field(max_length=20_000)] = Field(default_factory=list)
    removed_chunks: Annotated[list[str], Field(max_length=20_000)] = Field(default_factory=list)
    unchanged_chunks: int = Field(ge=0)


def build_global_snapshot(corpus: LoadedCorpus) -> CorpusGlobalSnapshot:
    lineage = [
        LineageEntry(
            domain=chunk.domain,
            source_id=chunk.source_id,
            document_id=chunk.document_id,
            document_version=chunk.document_version,
            chunk_id=chunk.chunk_id,
            fragment_id=chunk.fragment_id,
            chunk_checksum=chunk.checksum,
            embedding_model=chunk.embedding_model,
            embedding_dimension=chunk.embedding_dimension,
        )
        for chunk in sorted(corpus.repository.all_chunks(), key=lambda item: item.chunk_id)
    ]
    stable = json.dumps(
        [entry.model_dump(mode="json") for entry in lineage],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = "sha256:" + hashlib.sha256(stable.encode()).hexdigest()
    versions = corpus.corpus_versions
    return CorpusGlobalSnapshot(
        version="core-corpus-snapshot-2026-07-30",
        generated_at="2026-07-30T15:00:00Z",
        corpus_versions=versions,
        chunk_counts={
            domain: sum(1 for entry in lineage if entry.domain is domain) for domain in versions
        },
        lineage=lineage,
        digest=digest,
    )


def diff_snapshots(previous: CorpusGlobalSnapshot, current: CorpusGlobalSnapshot) -> CorpusDiff:
    before = {entry.chunk_id for entry in previous.lineage}
    after = {entry.chunk_id for entry in current.lineage}
    return CorpusDiff(
        previous_version=previous.version,
        current_version=current.version,
        added_chunks=sorted(after - before),
        removed_chunks=sorted(before - after),
        unchanged_chunks=len(before & after),
    )


def smoke_snapshot(snapshot: CorpusGlobalSnapshot) -> list[str]:
    """Gate mínimo previo a activación: cinco versiones, chunks y lineage coherente."""
    problems: list[str] = []
    missing = sorted(domain.value for domain in Domain if domain not in snapshot.corpus_versions)
    if missing:
        problems.append(f"faltan dominios en el snapshot: {missing}")
    empty = sorted(domain.value for domain, count in snapshot.chunk_counts.items() if count <= 0)
    if empty:
        problems.append(f"dominios sin chunks: {empty}")
    if sum(snapshot.chunk_counts.values()) != len(snapshot.lineage):
        problems.append("los conteos por dominio no coinciden con el lineage")
    return problems


def export_snapshot(snapshot: CorpusGlobalSnapshot, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot.model_dump(mode="json"), indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "CorpusDiff",
    "CorpusGlobalSnapshot",
    "LineageEntry",
    "build_global_snapshot",
    "diff_snapshots",
    "export_snapshot",
    "smoke_snapshot",
]
