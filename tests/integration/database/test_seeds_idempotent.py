"""Prueba: seeds repetidos — re-ejecutar el seed de demo no duplica filas
(criterio de aceptación "Seeds no duplican", sección 13 del doc de Daher)."""
from pathlib import Path

import pytest

from .conftest import new_conn

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_FILE = REPO_ROOT / "supabase" / "migrations" / "20260504140000_seeds_demo.sql"

# Cada consulta cuenta específicamente las filas que planta el seed de demo,
# para que el resultado no dependa de datos creados por otras pruebas.
SCOPED_COUNTS = {
    "tenants": "select count(*) from public.tenants where slug = 'gobierno-demo'",
    "plans": "select count(*) from public.plans where code = 'enterprise'",
    "modules": (
        "select count(*) from public.modules where code in "
        "('vehiculos','ayuntamiento_empresas','registro_civil','salud','ganaderia')"
    ),
    "branches": (
        "select count(*) from public.branches b join public.tenants t "
        "on t.id = b.tenant_id where t.slug = 'gobierno-demo' and b.code = 'MOD-CENTRO'"
    ),
    "roles": (
        "select count(*) from public.roles where tenant_id is null "
        "and code in ('admin','citizen')"
    ),
    "sources": "select count(*) from public.sources where checksum = 'hash_vehiculos_001'",
    "documents": (
        "select count(*) from public.documents where title = "
        "'Requisitos para Renovación de Licencia de Conducir'"
    ),
}


def _counts(conn) -> dict:
    return {name: conn.execute(query).fetchone()[0] for name, query in SCOPED_COUNTS.items()}


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

        conn.execute(seed_sql)
        after = _counts(conn)

        assert after == before, (
            f"re-ejecutar el seed duplicó filas: antes={before} despues={after}"
        )
    finally:
        conn.close()
