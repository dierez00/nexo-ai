"""Prueba: el seed de Vehículos/Salud/Empresas
(`20260504190000_rag_seed_vehiculos_salud_empresas.sql`) no duplica filas al
reejecutarse (mismo criterio de aceptación "Seeds no duplican" que
`test_seeds_idempotent.py`), y que `match_chunks` filtra por dominio sobre
estos datos reales, tal como exige "RAG filtra dominio/institución/vigencia"
(sección 13 del doc de Daher)."""
from pathlib import Path

import pytest

from .conftest import new_conn

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_FILE = REPO_ROOT / "supabase" / "migrations" / "20260504190000_rag_seed_vehiculos_salud_empresas.sql"

SOURCE_CHECKSUMS = (
    "hash_vehiculos_001", "hash_vehiculos_002", "hash_vehiculos_003",
    "hash_salud_001", "hash_salud_002", "hash_salud_003",
    "hash_empresas_001", "hash_empresas_002", "hash_empresas_003",
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
        assert before["sources"] == len(SOURCE_CHECKSUMS)

        conn.execute(seed_sql)
        after = _counts(conn)

        assert after == before, (
            f"re-ejecutar el seed duplicó filas: antes={before} despues={after}"
        )
    finally:
        conn.close()


@pytest.mark.integration
def test_match_chunks_filters_salud_documents_by_domain():
    conn = new_conn()
    try:
        conn.execute(SEED_FILE.read_text(encoding="utf-8"))

        tenant_id, content = conn.execute(
            "select d.tenant_id, d.content_raw from public.documents d "
            "join public.sources s on s.id = d.source_id "
            "where s.checksum = 'hash_salud_001' and d.title = 'Atención Prioritaria en Salud Mental'"
        ).fetchone()

        rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 10, filter_domain := 'salud', filter_tenant_id := %s)",
            (content, tenant_id),
        ).fetchall()

        contents = {r[0] for r in rows}
        assert content in contents

        other_domain_rows = conn.execute(
            "select content from public.match_chunks("
            "query_embedding := public.fake_embedding(%s), match_threshold := 0.0, "
            "match_count := 10, filter_domain := 'ayuntamiento_empresas', filter_tenant_id := %s)",
            (content, tenant_id),
        ).fetchall()
        assert content not in {r[0] for r in other_domain_rows}
    finally:
        conn.close()
