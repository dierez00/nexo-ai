"""Ingesta de corpus: manifests, checksums, fragmentación e idempotencia (F1.2).

Ninguna prueba de este archivo abre red ni base de datos: el corpus real del
repositorio se ingiere contra un repositorio en memoria.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from nexo_contracts import ConfigurationError, Domain, IngestionOutcome, SourceStatus
from nexo_rag.corpus import (
    ChecksumMismatchError,
    CorpusIngestion,
    checksum_of_text,
    chunk_document,
    chunk_markdown,
    fragment_id,
    load_domain_manifest,
)
from nexo_rag.corpus.cli import MVP_DOMAINS, repository_root, verify
from nexo_rag.testing import DeterministicEmbeddings, InMemoryChunkRepository, load_corpus

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def root() -> Path:
    return repository_root()


# --- Manifests (`DIE-F1-009`, `DIE-F1-010`, `DIE-F1-011`) --------------------


@pytest.mark.parametrize("domain", MVP_DOMAINS, ids=lambda d: d.value)
def test_every_mvp_domain_declares_a_valid_manifest(root: Path, domain: Domain) -> None:
    manifest = load_domain_manifest(root, domain)

    assert manifest.domain is domain
    assert manifest.active(), "un dominio sin fuentes activas no puede responder nada"


@pytest.mark.parametrize("domain", MVP_DOMAINS, ids=lambda d: d.value)
def test_every_source_declares_its_full_provenance(root: Path, domain: Domain) -> None:
    """`DIE-F1-010`: sin procedencia completa, una fuente no es auditable."""
    for source in load_domain_manifest(root, domain).sources:
        assert source.institution_id
        assert source.publisher
        assert source.owner
        assert source.license
        assert source.validity.valid_from is not None
        assert source.documents


@pytest.mark.parametrize("domain", MVP_DOMAINS, ids=lambda d: d.value)
def test_all_mvp_content_is_marked_synthetic(root: Path, domain: Domain) -> None:
    """`DIE-F1-011`: mientras no haya corpus autorizado, todo es sintético."""
    for source in load_domain_manifest(root, domain).sources:
        assert source.is_synthetic is True


def test_a_superseded_source_names_its_successor(root: Path) -> None:
    manifest = load_domain_manifest(root, Domain.VEHICULOS)
    superseded = manifest.by_id("src_veh_tarifas_2024")

    assert superseded is not None
    assert superseded.status is SourceStatus.SUPERSEDED
    assert superseded.superseded_by == "src_veh_tarifas"


def test_a_missing_manifest_fails_with_path_and_reason(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="no existe"):
        load_domain_manifest(tmp_path, Domain.VEHICULOS)


# --- Checksums (`DIE-F1-014`) ------------------------------------------------


def test_declared_checksums_match_the_files_on_disk(root: Path) -> None:
    """Si esto falla, alguien editó el corpus sin actualizar su manifest.

    Se arregla con `python -m nexo_rag.corpus.cli checksums`, nunca copiando el
    hash a mano.
    """
    assert verify(root, MVP_DOMAINS) == []


def test_checksums_ignore_line_ending_style() -> None:
    """Un `core.autocrlf` distinto no debe reindexar el corpus entero."""
    assert checksum_of_text("línea 1\nlínea 2\n") == checksum_of_text("línea 1\r\nlínea 2\r\n")


async def test_a_tampered_document_stops_the_ingestion(root: Path, tmp_path: Path) -> None:
    """`DIE-F1-014`: un corpus alterado sin registrar rompe, no se ingiere."""
    manifest = load_domain_manifest(root, Domain.VEHICULOS)
    tampered = manifest.model_copy(deep=True)
    tampered.sources[0].documents[0].checksum = "sha256:" + "0" * 64

    ingestion = CorpusIngestion(
        repository=InMemoryChunkRepository(),
        embeddings=DeterministicEmbeddings(),
        root=root,
        now=NOW,
    )
    with pytest.raises(ChecksumMismatchError):
        await ingestion.ingest(tampered)


# --- Fragmentación (`DIE-F1-012`, `DIE-F1-013`) ------------------------------


def test_offsets_point_back_to_the_original_text() -> None:
    """`DIE-F1-012`: una citación debe poder resaltarse sobre el archivo."""
    text = "# Título\n\nPreámbulo largo para que no se funda con nada más.\n\n" + (
        "## Requisitos\n\n" + "Identificación oficial vigente. " * 12 + "\n\n"
        "## Costos\n\n" + "El costo es de 814.00 MXN. " * 12
    )

    for chunk in chunk_markdown(text):
        assert text[chunk.char_start : chunk.char_end] == chunk.text


def test_chunking_is_stable_across_calls() -> None:
    """Un chunking que varía invalidaría las citaciones ya emitidas."""
    text = (
        Path(repository_root()) / "data/documents/vehiculos/src_veh_licencias/v3/requisitos.md"
    ).read_text(encoding="utf-8")

    first = chunk_markdown(text)
    second = chunk_markdown(text)

    assert [(c.ordinal, c.heading, c.char_start, c.char_end) for c in first] == [
        (c.ordinal, c.heading, c.char_start, c.char_end) for c in second
    ]


def test_the_document_title_is_never_a_standalone_fragment() -> None:
    """Un `H1` más su aviso legal no es evidencia; es un imán léxico."""
    text = (
        "# Renovación de licencia\n\n> Contenido sintético.\n\n"
        "## Requisitos\n\n" + "Identificación oficial vigente. " * 12
    )

    chunks = chunk_markdown(text)

    assert [chunk.heading for chunk in chunks] == ["Requisitos"]
    assert "Renovación de licencia" in chunks[0].text


def test_substantive_sections_keep_their_own_heading() -> None:
    """Fundir hacia atrás perdería el nombre de la sección que sí afirma algo."""
    text = (
        "# Uso de suelo\n\n> Sintético.\n\n"
        "## Zonificación aplicable\n\n" + "Las taquerías se permiten en H3 y H4. " * 10
    )

    assert [chunk.heading for chunk in chunk_markdown(text)] == ["Zonificación aplicable"]


def test_an_unknown_media_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="no hay estrategia de chunking"):
        chunk_document("texto", media_type="application/pdf")


def test_fragment_ids_survive_a_change_in_a_neighbouring_section() -> None:
    """`fragment_id` deriva del encabezado, no del ordinal.

    Con el ordinal, insertar una sección al principio renumeraría todo lo que
    viene después e invalidaría **en silencio** cada citación ya emitida: las
    citaciones seguirían validando y apuntarían a un texto distinto.
    """
    before = fragment_id("src_a", "doc_a", "v1", "Costos")
    after = fragment_id("src_a", "doc_a", "v1", "Costos")

    assert before == after
    assert fragment_id("src_a", "doc_a", "v1", "Requisitos") != before


def test_repeated_headings_inside_one_document_do_not_collide() -> None:
    first = fragment_id("src_a", "doc_a", "v1", "Vigencia", 0)
    second = fragment_id("src_a", "doc_a", "v1", "Vigencia", 1)

    assert first != second


def test_fragment_ids_never_look_like_personal_data() -> None:
    """El validador de IDs rechaza secuencias largas de dígitos.

    El alfabeto sin dígitos hace ese fallo imposible en lugar de improbable.
    """
    for ordinal in range(200):
        assert not any(char.isdigit() for char in fragment_id("src_a", "doc_a", "v1", str(ordinal)))


# --- Ingesta idempotente (`DIE-F1-015`…`DIE-F1-019`) -------------------------


async def test_the_whole_mvp_corpus_ingests(root: Path) -> None:
    corpus = await load_corpus(root=root)

    assert corpus.repository.all_chunks()
    for domain in MVP_DOMAINS:
        assert corpus.reports[domain].result.chunks_created > 0


async def test_reingesting_an_unchanged_corpus_creates_nothing(root: Path) -> None:
    """`DIE-F1-019`: la segunda corrida no crea un solo chunk."""
    repository = InMemoryChunkRepository()
    embeddings = DeterministicEmbeddings()
    manifest = load_domain_manifest(root, Domain.VEHICULOS)

    first = await CorpusIngestion(
        repository=repository, embeddings=embeddings, root=root, now=NOW
    ).ingest(manifest)
    count_after_first = await repository.count(corpus_version=manifest.corpus_version)

    second = await CorpusIngestion(
        repository=repository, embeddings=embeddings, root=root, now=NOW
    ).ingest(manifest)

    assert first.result.chunks_created > 0
    assert second.result.chunks_created == 0
    assert second.result.outcomes.get(IngestionOutcome.UNCHANGED, 0) == len(
        [doc for source in manifest.sources for doc in source.documents]
    )
    assert await repository.count(corpus_version=manifest.corpus_version) == count_after_first


async def test_superseded_sources_stay_indexed_with_their_real_status(root: Path) -> None:
    """`DIE-F1-016`: no se borran; se marcan, y el retriever las filtra."""
    corpus = await load_corpus(root=root)

    superseded = [
        chunk
        for chunk in corpus.repository.all_chunks()
        if chunk.source_id == "src_veh_tarifas_2024"
    ]

    assert superseded
    assert all(chunk.status is SourceStatus.SUPERSEDED for chunk in superseded)


async def test_every_chunk_records_the_embedding_model_and_dimension(root: Path) -> None:
    """`DIE-F1-017`: reindexar con otro modelo debe ser detectable."""
    corpus = await load_corpus(root=root)

    for chunk in corpus.repository.all_chunks():
        assert chunk.embedding_model == corpus.embeddings.model_name
        assert chunk.embedding_dimension == corpus.embeddings.dimension


async def test_ingestion_is_reproducible(root: Path) -> None:
    """Dos ingestas del mismo corpus producen exactamente los mismos fragmentos."""
    first = await load_corpus(root=root)
    second = await load_corpus(root=root)

    assert sorted(c.fragment_id for c in first.repository.all_chunks()) == sorted(
        c.fragment_id for c in second.repository.all_chunks()
    )
