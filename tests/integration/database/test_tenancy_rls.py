"""Prueba: tenancy — RLS aísla estrictamente los datos de un tenant frente
a usuarios autenticados de otro tenant (sección 12 y criterios de
aceptación, sección 13: "RAG filtra dominio/institución/vigencia")."""
import pytest

from .conftest import (
    act_as,
    act_as_admin,
    cleanup_tenant,
    make_authenticated_actor,
    make_branch,
    make_tenant,
    new_conn,
)


@pytest.mark.integration
def test_authenticated_user_cannot_see_other_tenant_rows(admin_conn):
    tenant_a = make_tenant(admin_conn)
    tenant_b = make_tenant(admin_conn)

    branch_a = make_branch(admin_conn, tenant_a)
    admin_conn.execute(
        "insert into public.sources (tenant_id, domain, name, checksum, status) "
        "values (%s, 'vehiculos', 'Fuente A', 'chk-a', 'active')",
        (tenant_a,),
    )
    admin_conn.execute(
        "insert into public.conversations (tenant_id, channel, status) "
        "values (%s, 'web', 'active')",
        (tenant_a,),
    )
    admin_conn.execute(
        "insert into public.appointments "
        "(tenant_id, branch_id, module_code, service_name, time_range, status) "
        "values (%s, %s, 'vehiculos', 'renovacion', "
        "tstzrange('2026-08-03 09:00+00', '2026-08-03 09:30+00'), 'hold')",
        (tenant_a, branch_a),
    )

    auth_user_b, _user_b = make_authenticated_actor(admin_conn, tenant_b)

    session = new_conn()
    try:
        act_as(session, auth_user_b)

        sources_seen = session.execute(
            "select count(*) from public.sources where tenant_id = %s", (tenant_a,)
        ).fetchone()[0]
        conversations_seen = session.execute(
            "select count(*) from public.conversations where tenant_id = %s", (tenant_a,)
        ).fetchone()[0]
        appointments_seen = session.execute(
            "select count(*) from public.appointments where tenant_id = %s", (tenant_a,)
        ).fetchone()[0]

        assert sources_seen == 0, "RLS debe ocultar sources de otro tenant"
        assert conversations_seen == 0, "RLS debe ocultar conversations de otro tenant"
        assert appointments_seen == 0, "RLS debe ocultar appointments de otro tenant"

        act_as_admin(session)
    finally:
        session.close()
        cleanup_tenant(admin_conn, tenant_a)
        cleanup_tenant(admin_conn, tenant_b, [auth_user_b])


@pytest.mark.integration
def test_authenticated_user_sees_own_tenant_rows(admin_conn):
    tenant_a = make_tenant(admin_conn)
    admin_conn.execute(
        "insert into public.sources (tenant_id, domain, name, checksum, status) "
        "values (%s, 'vehiculos', 'Fuente propia', 'chk-own', 'active')",
        (tenant_a,),
    )
    auth_user_a, _user_a = make_authenticated_actor(admin_conn, tenant_a)

    session = new_conn()
    try:
        act_as(session, auth_user_a)
        own_sources = session.execute(
            "select count(*) from public.sources where tenant_id = %s", (tenant_a,)
        ).fetchone()[0]
        assert own_sources == 1, "el usuario debe ver las filas de su propio tenant"
        act_as_admin(session)
    finally:
        session.close()
        cleanup_tenant(admin_conn, tenant_a, [auth_user_a])
