"""Prueba: FK/check/unique/exclude — la base de datos rechaza filas que
violan las constraints declaradas en las migraciones (sección 12)."""
import psycopg
import pytest

from .conftest import cleanup_tenant, make_branch, make_tenant


@pytest.fixture
def tenant(admin_conn):
    tid = make_tenant(admin_conn)
    yield tid
    cleanup_tenant(admin_conn, tid)


@pytest.mark.integration
def test_foreign_key_violation_rejected(admin_conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        admin_conn.execute(
            "insert into public.branches (tenant_id, code, name, status) "
            "values (999999999, 'X', 'X', 'active')"
        )


@pytest.mark.integration
def test_check_violation_rejected(admin_conn, tenant):
    with pytest.raises(psycopg.errors.CheckViolation):
        admin_conn.execute(
            "insert into public.tenants (name, slug, status) values "
            "('bad', 'bad-status-tenant', 'not-a-real-status')"
        )


@pytest.mark.integration
def test_unique_violation_rejected(admin_conn, tenant):
    admin_conn.execute(
        "insert into public.branches (tenant_id, code, name, status) "
        "values (%s, 'DUP', 'first', 'active')",
        (tenant,),
    )
    with pytest.raises(psycopg.errors.UniqueViolation):
        admin_conn.execute(
            "insert into public.branches (tenant_id, code, name, status) "
            "values (%s, 'DUP', 'second', 'active')",
            (tenant,),
        )


@pytest.mark.integration
def test_exclude_violation_rejected_for_overlapping_appointments(admin_conn, tenant):
    branch_id = make_branch(admin_conn, tenant)
    admin_conn.execute(
        "insert into public.appointments "
        "(tenant_id, branch_id, module_code, service_name, time_range, status) "
        "values (%s, %s, 'vehiculos', 'renovacion', "
        "tstzrange('2026-08-01 10:00+00', '2026-08-01 10:30+00'), 'hold')",
        (tenant, branch_id),
    )
    with pytest.raises(psycopg.errors.ExclusionViolation):
        admin_conn.execute(
            "insert into public.appointments "
            "(tenant_id, branch_id, module_code, service_name, time_range, status) "
            "values (%s, %s, 'vehiculos', 'renovacion', "
            "tstzrange('2026-08-01 10:15+00', '2026-08-01 10:45+00'), 'hold')",
            (tenant, branch_id),
        )
