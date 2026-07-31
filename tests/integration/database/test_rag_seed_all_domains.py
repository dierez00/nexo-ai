"""Prueba: el seed amplio de los 5 dominios
(`20260731120000_rag_seed_domain_datasets_full.sql`) no duplica filas al
reejecutarse (criterio "Seeds no duplican"), `match_chunks` filtra por dominio
sobre estos datos reales y excluye las fuentes vencidas/sustituidas
(criterio "RAG filtra dominio/institución/vigencia", sección 13 del doc de
Daher). Complementa `test_rag_seed_domain_expansion.py` (que solo cubría 3
dominios) y `test_rag_vigencia.py`."""
from pathlib import Path

import pytest

from .conftest import new_conn

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_FILE = (
    REPO_ROOT / "supabase" / "migrations"
    / "20260731120000_rag_seed_domain_datasets_full.sql"
)

# Los 25 checksums sintéticos que planta el seed (5 por dominio, el último de
# cada bloque es la fuente vencida/sustituida usada para el filtro de vigencia).
SOURCE_CHECKSUMS = (
    "syn_veh_001", "syn_veh_002", "syn_veh_003", "syn_veh_004", "syn_veh_005",
    "syn_emp_001", "syn_emp_002", "syn_emp_003", "syn_emp_004", "syn_emp_005",
    "syn_rc_001", "syn_rc_002", "syn_rc_003", "syn_rc_004", "syn_rc_005",
    "syn_sal_001", "syn_sal_002", "syn_sal_003", "syn_sal_004", "syn_sal_005",
    "syn_gan_001", "syn_gan_002", "syn_gan_003", "syn_gan_004", "syn_gan_005",
)

SCOPED_COUNTS = {
    "sources": (
        "select count(*) from public.sources where checksum = any(%(checksums)s)"
    ),
    "documents": (
        "select count(*) from public.documents d "
        "join public.sources s on s.id = d.source_id "
        "where s.checksum = any(%(checksums)s)"
    ),
    "chunks": (
        "select count(*) from public.chunks c "
        "join public.documents d on d.id = c.document_id "
        "join public.sources s on s.id = d.source_id "
        "where s.checksum = any(%(checksums)s)"
    ),
}


def _counts(conn) -> dict:
    return {
        name: conn.execute(query, {"checksums": list(SOURCE_CHECKSUMS)}).fetchone()[0]
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
        # Una fila de sources por cada checksum sembrado.
        assert before["sources"] == len(SOURCE_CHECKSUMS)
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

        # Documento activo del dominio salud.
        tenant_id, content = conn.execute(
            "select d.tenant_id, d.content_raw from public.documents d "
            "join public.sources s on s.id = d.source_id "
            "where s.checksum = 'syn_sal_001' "
            "and d.title = 'Unidades por Municipio y Afiliacion (demo)'"
        ).fetchone()

        salud_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 25, filter_domain := 'salud', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (content, tenant_id),
        ).fetchall()
        assert content in {r[0] for r in salud_rows}

        # El mismo contenido no debe aparecer al filtrar por otro dominio.
        gan_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 25, filter_domain := 'ganaderia', filter_tenant_id := %s, "
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
            "where s.checksum = 'syn_veh_005'"
        ).fetchone()

        # Aun consultando con su propio embedding (similitud máxima), no aparece:
        # match_chunks solo devuelve fuentes con status en filter_status ('active').
        rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 25, filter_domain := 'vehiculos', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (stale_content, tenant_id),
        ).fetchall()
        contents = {r[0] for r in rows}
        assert stale_content not in contents

        # Contraste: un documento activo del mismo dominio sí es recuperable.
        active_content = conn.execute(
            "select d.content_raw from public.documents d "
            "join public.sources s on s.id = d.source_id "
            "where s.checksum = 'syn_veh_001' "
            "and d.title = 'Renovación de Licencia Tipo A — Requisitos (demo)'"
        ).fetchone()[0]
        active_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 25, filter_domain := 'vehiculos', filter_tenant_id := %s, "
            "filter_status := array['active']::text[])",
            (active_content, tenant_id),
        ).fetchall()
        assert active_content in {r[0] for r in active_rows}
    finally:
        conn.close()
