"""Prueba: idempotencia — `actions.idempotency_key` es única, por lo que un
reintento con la misma clave nunca produce una segunda ejecución
registrada (sección 12, "idempotencia")."""
import psycopg
import pytest

from .conftest import cleanup_tenant, make_tenant


@pytest.fixture
def tenant(admin_conn):
    tid = make_tenant(admin_conn)
    yield tid
    cleanup_tenant(admin_conn, tid)


@pytest.mark.integration
def test_duplicate_idempotency_key_rejected(admin_conn, tenant):
    key = "idem-key-001"
    admin_conn.execute(
        "insert into public.actions (tenant_id, idempotency_key, action_name, status) "
        "values (%s, %s, 'vehiculos.reservar_cita', 'pending')",
        (tenant, key),
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        admin_conn.execute(
            "insert into public.actions (tenant_id, idempotency_key, action_name, status) "
            "values (%s, %s, 'vehiculos.reservar_cita', 'pending')",
            (tenant, key),
        )

    count = admin_conn.execute(
        "select count(*) from public.actions where idempotency_key = %s", (key,)
    ).fetchone()[0]
    assert count == 1, "solo debe existir una fila para la idempotency_key dada"
