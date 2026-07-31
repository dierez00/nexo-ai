"""Prueba: índices/EXPLAIN — los índices declarados en las migraciones
existen y son utilizables por el planificador para las queries críticas
(sección 12 y checklist "Índices y query plans", sección 15).

Nota: con tablas pequeñas/vacías como en un entorno de test, el
planificador de costos de Postgres puede preferir un Seq Scan aunque el
índice exista (es más barato en pocas filas). Por eso: (1) primero se
verifica estructuralmente que el índice existe en `pg_indexes`, y (2) para
confirmar que la query es *compatible* con el índice (no solo que existe),
se fuerza `enable_seqscan = off` a nivel de transacción y se confirma que
el plan resultante referencia el índice — es decir, que hay un camino de
índice válido para esa query, no que el optimizador lo elegiría siempre."""
import pytest

EXPECTED_INDEXES = {
    "sources": ["idx_sources_tenant_domain"],
    "chunks": ["idx_chunks_embedding_hnsw", "idx_chunks_tenant_domain"],
    "appointments": ["idx_appointments_tenant_branch", "idx_appointments_status"],
    "actions": ["idx_actions_idempotency"],
    "audit_logs": ["idx_audit_logs_tenant_date"],
    "runs": ["idx_runs_tenant_trace"],
}


@pytest.mark.integration
def test_expected_indexes_exist(admin_conn):
    rows = admin_conn.execute(
        "select tablename, indexname from pg_indexes where schemaname = 'public'"
    ).fetchall()
    by_table: dict[str, set[str]] = {}
    for table, index in rows:
        by_table.setdefault(table, set()).add(index)

    missing = []
    for table, indexes in EXPECTED_INDEXES.items():
        for index in indexes:
            if index not in by_table.get(table, set()):
                missing.append(f"{table}.{index}")

    assert not missing, f"índices esperados faltantes: {missing}"


def _explain_forcing_index(conn, query: str, params: tuple = ()) -> str:
    conn.execute("begin")
    try:
        conn.execute("set local enable_seqscan = off")
        rows = conn.execute(f"explain {query}", params).fetchall()
        return "\n".join(r[0] for r in rows)
    finally:
        conn.execute("rollback")


@pytest.mark.integration
def test_sources_query_can_use_tenant_domain_index(admin_conn):
    plan = _explain_forcing_index(
        admin_conn,
        "select id from public.sources where tenant_id = %s and domain = %s and status = 'active'",
        (1, "vehiculos"),
    )
    # Con enable_seqscan=off el planificador puede elegir cualquier índice
    # que arranque en tenant_id (idx_sources_tenant_domain o la unique
    # constraint sources_tenant_checksum_key añadida en el fix de
    # idempotencia) — lo que importa es que exista un camino de índice, no
    # cuál en concreto elija el optimizador.
    assert "Seq Scan" not in plan, plan
    assert "Index" in plan, plan


@pytest.mark.integration
def test_appointments_query_can_use_tenant_branch_index(admin_conn):
    plan = _explain_forcing_index(
        admin_conn,
        "select id from public.appointments where tenant_id = %s and branch_id = %s",
        (1, 1),
    )
    assert "idx_appointments_tenant_branch" in plan, plan


@pytest.mark.integration
def test_actions_idempotency_lookup_can_use_index(admin_conn):
    plan = _explain_forcing_index(
        admin_conn,
        "select id from public.actions where idempotency_key = %s",
        ("some-key",),
    )
    assert "idx_actions_idempotency" in plan or "actions_idempotency_key_key" in plan, plan
