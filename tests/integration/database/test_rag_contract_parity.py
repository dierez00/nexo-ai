"""Paridad RAG persistente contra el snapshot offline.

La base no decide otro contrato: almacena y filtra los mismos identificadores,
lineage, status, vigencia y tenant que `nexo_contracts.Chunk`.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import date

import pytest

from nexo_contracts import SourceStatus
from nexo_rag.corpus import build_global_snapshot
from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root
from nexo_rag.testing import load_corpus

from .conftest import cleanup_tenant, make_tenant

DIM = 1536
VALID_AT = date(2026, 7, 30)


def _vec(value: float = 0.1) -> str:
    return "[" + ",".join([str(value)] * DIM) + "]"


def _checksum(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _load_offline():
    return asyncio.run(load_corpus(root=repository_root(), domains=CORE_DOMAINS))


def _source_id(conn, tenant_id: int, chunk) -> int:
    row = conn.execute(
        """
        insert into public.sources (
          tenant_id, domain, name, version, status, valid_from, valid_to, checksum,
          source_key, institution_id, owner, license, verified_at, is_synthetic
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Diego', 'demo',
                '2026-07-30T15:00:00Z', true)
        on conflict (tenant_id, source_key) where source_key is not null do update
        set status = excluded.status
        returning id
        """,
        (
            tenant_id,
            chunk.domain.value,
            chunk.source_id,
            chunk.document_version,
            chunk.status.value,
            chunk.validity.valid_from,
            chunk.validity.valid_to,
            _checksum(chunk.source_id),
            chunk.source_id,
            chunk.institution_id,
        ),
    ).fetchone()
    return row[0]


def _document_id(conn, tenant_id: int, source_id: int, chunk) -> int:
    row = conn.execute(
        """
        insert into public.documents (
          tenant_id, source_id, title, document_key, source_key, media_type,
          original_path, document_version
        )
        values (%s, %s, %s, %s, %s, 'text/markdown', %s, %s)
        on conflict (tenant_id, document_key) where document_key is not null do update
        set document_version = excluded.document_version
        returning id
        """,
        (
            tenant_id,
            source_id,
            chunk.document_id,
            chunk.document_id,
            chunk.source_id,
            f"data/documents/{chunk.domain.value}/{chunk.source_id}/{chunk.document_version}",
            chunk.document_version,
        ),
    ).fetchone()
    return row[0]


def _insert_chunk(conn, tenant_id: int, document_id: int, chunk) -> None:
    conn.execute(
        """
        insert into public.chunks (
          tenant_id, document_id, domain, chunk_index, content, embedding, checksum,
          chunk_key, fragment_key, source_key, document_key, document_version,
          heading, char_start, char_end, chunk_checksum, source_status, valid_from,
          valid_to, institution_id, embedding_model, embedding_dimension
        )
        values (
          %s, %s, %s, %s, %s, %s::vector(1536), %s,
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        on conflict (tenant_id, chunk_key) where chunk_key is not null do update
        set chunk_checksum = excluded.chunk_checksum,
            content = excluded.content
        """,
        (
            tenant_id,
            document_id,
            chunk.domain.value,
            chunk.ordinal,
            chunk.text,
            _vec(),
            chunk.checksum,
            chunk.chunk_id,
            chunk.fragment_id,
            chunk.source_id,
            chunk.document_id,
            chunk.document_version,
            chunk.heading,
            chunk.char_start,
            chunk.char_end,
            chunk.checksum,
            chunk.status.value,
            chunk.validity.valid_from,
            chunk.validity.valid_to,
            chunk.institution_id,
            chunk.embedding_model,
            chunk.embedding_dimension,
        ),
    )


def _ingest(conn, tenant_id: int, chunks) -> None:
    documents: dict[tuple[int, str], int] = {}
    for chunk in chunks:
        sid = _source_id(conn, tenant_id, chunk)
        key = (sid, chunk.document_id)
        did = documents.get(key)
        if did is None:
            did = _document_id(conn, tenant_id, sid, chunk)
            documents[key] = did
        _insert_chunk(conn, tenant_id, did, chunk)


@pytest.mark.integration
def test_persistent_rag_matches_offline_snapshot_lineage_and_filters(admin_conn) -> None:
    tenant_a = make_tenant(admin_conn)
    tenant_b = make_tenant(admin_conn)
    try:
        offline = _load_offline()
        chunks = offline.repository.all_chunks()
        snapshot = build_global_snapshot(offline)
        _ingest(admin_conn, tenant_a, chunks)
        _ingest(admin_conn, tenant_b, chunks)

        rows = admin_conn.execute(
            """
            select domain, source_key, document_key, document_version, chunk_key,
                   fragment_key, chunk_checksum, embedding_model, embedding_dimension
            from public.chunks
            where tenant_id = %s
            order by chunk_key
            """,
            (tenant_a,),
        ).fetchall()

        assert [row[4] for row in rows] == [entry.chunk_id for entry in snapshot.lineage]
        assert [row[5] for row in rows] == [entry.fragment_id for entry in snapshot.lineage]
        assert [row[6] for row in rows] == [entry.chunk_checksum for entry in snapshot.lineage]

        active_expected = [
            chunk
            for chunk in chunks
            if chunk.status is SourceStatus.ACTIVE and chunk.validity.covers(VALID_AT)
        ]
        active_rows = admin_conn.execute(
            """
            select chunk_id, source_id
            from public.match_chunks(
              query_embedding := %s::vector(1536),
              match_threshold := 0.0,
              match_count := 200,
              filter_domain := null,
              filter_tenant_id := %s,
              filter_valid_at := %s,
              filter_status := array['active']::text[]
            )
            """,
            (_vec(), tenant_a, VALID_AT),
        ).fetchall()
        assert {row[0] for row in active_rows} == {chunk.chunk_id for chunk in active_expected}

        allowed = active_expected[0].source_id
        allowlisted = admin_conn.execute(
            """
            select distinct source_id
            from public.match_chunks(
              query_embedding := %s::vector(1536),
              match_threshold := 0.0,
              match_count := 200,
              filter_tenant_id := %s,
              allowed_source_ids := %s::text[]
            )
            """,
            (_vec(), tenant_a, [allowed]),
        ).fetchall()
        assert {row[0] for row in allowlisted} == {allowed}

        tenant_b_count = admin_conn.execute(
            "select count(*) from public.chunks where tenant_id = %s",
            (tenant_b,),
        ).fetchone()[0]
        assert tenant_b_count == len(snapshot.lineage)
    finally:
        cleanup_tenant(admin_conn, tenant_a)
        cleanup_tenant(admin_conn, tenant_b)
