"""Prueba: el seed BULK sintético masivo
(`20260731130000_rag_seed_domain_datasets_bulk.sql`, generado por
`scripts/gen_rag_bulk_seed.py`) no duplica filas al reejecutarse
(criterio "Seeds no duplican"), `match_chunks` filtra por dominio sobre estos
datos y excluye las fuentes vencidas/sustituidas (criterio
"RAG filtra dominio/institución/vigencia", sección 13 del doc de Daher).

Acotado al namespace `bulk_%`, así que es independiente de los seeds `syn_*`
(`test_rag_seed_all_domains.py`) y `hash_*` (`test_rag_seed_domain_expansion.py`)."""
from pathlib import Path

import pytest

from .conftest import new_conn

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_FILE = (
    REPO_ROOT / "supabase" / "migrations"
    / "20260731130000_rag_seed_domain_datasets_bulk.sql"
)

# Debe coincidir con SOURCES_PER_DOMAIN * 5 en scripts/gen_rag_bulk_seed.py.
EXPECTED_SOURCES = 200

SCOPED_COUNTS = {
    "sources": (
        r"select count(*) from public.sources where checksum like 'bulk\_%'"
    ),
    "documents": (
        r"select count(*) from public.documents d "
        r"join public.sources s on s.id = d.source_id "
        r"where s.checksum like 'bulk\_%'"
    ),
    "chunks": (
        r"select count(*) from public.chunks c "
        r"join public.documents d on d.id = c.document_id "
        r"join public.sources s on s.id = d.source_id "
        r"where s.checksum like 'bulk\_%'"
    ),
}


def _counts(conn) -> dict:
    return {
        name: conn.execute(query).fetchone()[0]
        for name, query in SCOPED_COUNTS.items()
    }


@pytest.mark.integration
def test_seed_rerun_does_not_duplicate():
    conn = new_conn()
    try:
        seed_sql = SEED_FILE.read_text(encoding="utf-8")

        conn.execute(seed_sql)
        before = _counts(conn)
        assert all(v >= 1 for v in before.values()), (
            f"el seed debería haber insertado al menos una fila por tabla: {before}"
        )
        assert before["sources"] == EXPECTED_SOURCES
        # Un chunk por documento (un chunk_index = 0 por documento).
        assert before["chunks"] == before["documents"]

        conn.execute(seed_sql)
        after = _counts(conn)

        assert after == before, (
            f"re-ejecutar el seed duplicó filas: antes={before} despues={after}"
        )
    finally:
        conn.close()


@pytest.mark.integration
def test_match_chunks_filters_by_domain():
    conn = new_conn()
    try:
        conn.execute(SEED_FILE.read_text(encoding="utf-8"))

        # Documento activo del dominio salud (primera fuente bulk de salud).
        tenant_id, content = conn.execute(
            "select d.tenant_id, d.content_raw from public.documents d "
            "join public.sources s on s.id = d.source_id "
            "where s.checksum = 'bulk_sal_0001' "
            "order by d.id limit 1"
        ).fetchone()

        salud_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 50, filter_domain := 'salud', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (content, tenant_id),
        ).fetchall()
        assert content in {r[0] for r in salud_rows}

        # El mismo contenido no debe aparecer al filtrar por otro dominio.
        gan_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 50, filter_domain := 'ganaderia', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (content, tenant_id),
        ).fetchall()
        assert content not in {r[0] for r in gan_rows}
    finally:
        conn.close()


@pytest.mark.integration
def test_match_chunks_excludes_superseded_and_expired_sources():
    conn = new_conn()
    try:
        conn.execute(SEED_FILE.read_text(encoding="utf-8"))

        # Documento de una fuente SUSTITUIDA (status='superseded') de vehículos.
        tenant_id, stale_content = conn.execute(
            "select d.tenant_id, d.content_raw from public.documents d "
            "join public.sources s on s.id = d.source_id "
            "where s.checksum = 'bulk_veh_0009' order by d.id limit 1"
        ).fetchone()

        rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 50, filter_domain := 'vehiculos', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (stale_content, tenant_id),
        ).fetchall()
        assert stale_content not in {r[0] for r in rows}

        # Contraste: un documento activo del mismo dominio sí es recuperable.
        active_content = conn.execute(
            "select d.content_raw from public.documents d "
            "join public.sources s on s.id = d.source_id "
            "where s.checksum = 'bulk_veh_0001' order by d.id limit 1"
        ).fetchone()[0]
        active_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 50, filter_domain := 'vehiculos', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (active_content, tenant_id),
        ).fetchall()
        assert active_content in {r[0] for r in active_rows}
    finally:
        conn.close()
