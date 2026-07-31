"""Prueba: reservas concurrentes — dos citas solapadas insertadas en
paralelo (conexiones y threads separados) nunca coexisten; el constraint
GiST `appointments_no_overlap` garantiza que exactamente una sobreviva
(criterio de aceptación "Cero citas solapadas persisted", sección 13)."""
import threading

import psycopg
import pytest

from .conftest import cleanup_tenant, make_branch, make_tenant, new_conn


@pytest.mark.integration
def test_concurrent_overlapping_holds_only_one_succeeds(admin_conn):
    tenant_id = make_tenant(admin_conn)
    branch_id = make_branch(admin_conn, tenant_id)

    barrier = threading.Barrier(2)
    results = {}

    def try_insert(key: str, start: str, end: str):
        conn = new_conn()
        try:
            barrier.wait(timeout=10)
            conn.execute(
                "insert into public.appointments "
                "(tenant_id, branch_id, module_code, service_name, time_range, status) "
                "values (%s, %s, 'vehiculos', 'renovacion', tstzrange(%s, %s), 'hold')",
                (tenant_id, branch_id, start, end),
            )
            results[key] = "ok"
        except (psycopg.errors.ExclusionViolation, psycopg.errors.DeadlockDetected):
            results[key] = "rejected"
        except Exception as exc:  # pragma: no cover - unexpected failure surfaced in assert
            results[key] = f"error: {exc!r}"
        finally:
            conn.close()

    t1 = threading.Thread(
        target=try_insert,
        args=("a", "2026-08-02 09:00+00", "2026-08-02 09:30+00"),
    )
    t2 = threading.Thread(
        target=try_insert,
        args=("b", "2026-08-02 09:15+00", "2026-08-02 09:45+00"),
    )
    t1.start()
    t2.start()
    t1.join(timeout=15)
    t2.join(timeout=15)

    try:
        assert set(results.values()) == {"ok", "rejected"}, (
            f"se esperaba exactamente un insert exitoso y uno rechazado: {results}"
        )

        row = admin_conn.execute(
            "select count(*) from public.appointments where tenant_id = %s and status = 'hold'",
            (tenant_id,),
        ).fetchone()
        assert row[0] == 1, "debe persistir exactamente una cita tras el conflicto"
    finally:
        cleanup_tenant(admin_conn, tenant_id)
