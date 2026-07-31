import pytest

from nexo_contracts import Domain, SourceStatus
from nexo_rag.corpus import (
    CorpusIngestion,
    build_global_snapshot,
    diff_snapshots,
    load_domain_manifest,
    smoke_snapshot,
)
from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root
from nexo_rag.safety import detect_injection
from nexo_rag.testing import (
    DEFAULT_NOW,
    DeterministicEmbeddings,
    InMemoryChunkRepository,
    load_corpus,
)


@pytest.mark.anyio
async def test_global_snapshot_covers_five_domains_and_lineage() -> None:
    root = repository_root()
    snapshot = build_global_snapshot(await load_corpus(root=root, domains=CORE_DOMAINS))

    assert set(snapshot.corpus_versions) == set(Domain)
    assert smoke_snapshot(snapshot) == []
    assert snapshot.lineage
    assert snapshot.digest.startswith("sha256:")


@pytest.mark.anyio
async def test_core_reingestion_is_idempotent() -> None:
    root = repository_root()
    repository = InMemoryChunkRepository()
    embeddings = DeterministicEmbeddings()
    ingestion = CorpusIngestion(
        repository=repository,
        embeddings=embeddings,
        root=root,
        now=DEFAULT_NOW,
    )

    for domain in CORE_DOMAINS:
        await ingestion.ingest(load_domain_manifest(root, domain))
    count = len(repository.all_chunks())
    second = [await ingestion.ingest(load_domain_manifest(root, domain)) for domain in CORE_DOMAINS]

    assert len(repository.all_chunks()) == count
    assert sum(report.result.chunks_created for report in second) == 0


@pytest.mark.anyio
async def test_equal_snapshots_have_an_empty_diff() -> None:
    root = repository_root()
    snapshot = build_global_snapshot(await load_corpus(root=root, domains=CORE_DOMAINS))

    diff = diff_snapshots(snapshot, snapshot)

    assert diff.added_chunks == []
    assert diff.removed_chunks == []
    assert diff.unchanged_chunks == len(snapshot.lineage)


def test_each_core_domain_has_lifecycle_and_adversarial_sources() -> None:
    root = repository_root()
    expected_statuses = {
        SourceStatus.ACTIVE,
        SourceStatus.EXPIRED,
        SourceStatus.SUPERSEDED,
    }

    for domain in CORE_DOMAINS:
        manifest = load_domain_manifest(root, domain)
        assert expected_statuses <= {source.status for source in manifest.sources}

        active_documents = [
            root / document.path
            for source in manifest.active()
            for document in source.documents
        ]
        assert any(
            detect_injection(path.read_text(encoding="utf-8")) for path in active_documents
        ), f"{domain.value} debe incluir una fuente adversarial activa"
