"""Fixtures compartidas para las pruebas de integración de base de datos.

Requiere un stack local de Supabase corriendo (`npx supabase start`) con las
migraciones aplicadas (`npx supabase db reset`). La URL de conexión se toma
de la variable de entorno DATABASE_URL, con el valor por defecto que usa el
CLI de Supabase para el Postgres local.
"""
import os
import uuid

import psycopg
import pytest

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
)


def new_conn() -> psycopg.Connection:
    """Abre una conexión nueva e independiente (rol postgres, superusuario)."""
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    return conn


@pytest.fixture
def admin_conn():
    """Conexión superusuario para arrange/assert/cleanup, una por test."""
    conn = new_conn()
    try:
        yield conn
    finally:
        conn.close()


def make_tenant(conn, slug: str | None = None, status: str = "active") -> int:
    slug = slug or f"test-{uuid.uuid4().hex[:10]}"
    row = conn.execute(
        "insert into public.tenants (name, slug, status) values (%s, %s, %s) "
        "returning id",
        (f"Tenant {slug}", slug, status),
    ).fetchone()
    return row[0]


def make_branch(conn, tenant_id: int, code: str = "MAIN") -> int:
    row = conn.execute(
        "insert into public.branches (tenant_id, code, name, status) "
        "values (%s, %s, %s, 'active') returning id",
        (tenant_id, code, f"Branch {code}"),
    ).fetchone()
    return row[0]


def system_role_id(conn, code: str = "citizen") -> int:
    row = conn.execute(
        "select id from public.roles where tenant_id is null and code = %s", (code,)
    ).fetchone()
    if row is None:
        raise RuntimeError(
            f"system role '{code}' not found — did the seed migration run?"
        )
    return row[0]


def make_auth_user(conn, email: str | None = None) -> str:
    """Inserta una fila mínima en auth.users (sin pasar por GoTrue) y la
    retorna como uuid string, lista para usarse como auth_user_id."""
    user_id = str(uuid.uuid4())
    email = email or f"{user_id}@example.test"
    conn.execute(
        """
        insert into auth.users (
            id, instance_id, aud, role, email, encrypted_password,
            email_confirmed_at, created_at, updated_at,
            raw_app_meta_data, raw_user_meta_data
        ) values (
            %s, '00000000-0000-0000-0000-000000000000', 'authenticated',
            'authenticated', %s, '', now(), now(), now(), '{}'::jsonb, '{}'::jsonb
        )
        """,
        (user_id, email),
    )
    return user_id


def make_user(
    conn,
    tenant_id: int,
    auth_user_id: str,
    role_id: int,
    branch_id: int | None = None,
    email: str | None = None,
) -> int:
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.test"
    row = conn.execute(
        "insert into public.users (auth_user_id, tenant_id, branch_id, role_id, "
        "email, name, status) values (%s, %s, %s, %s, %s, 'Test User', 'active') "
        "returning id",
        (auth_user_id, tenant_id, branch_id, role_id, email),
    ).fetchone()
    return row[0]


def make_authenticated_actor(conn, tenant_id: int, branch_id: int | None = None):
    """Crea un auth.users + public.users listos para autenticar en la sesión,
    retorna (auth_user_id, user_id)."""
    role_id = system_role_id(conn, "citizen")
    auth_user_id = make_auth_user(conn)
    user_id = make_user(conn, tenant_id, auth_user_id, role_id, branch_id)
    return auth_user_id, user_id


def act_as(conn, auth_user_id: str) -> None:
    """Cambia la sesión actual al rol `authenticated` simulando el JWT de
    Supabase para ese auth_user_id, de modo que las políticas RLS que usan
    auth.uid()/current_tenant_id() se apliquen tal como en producción."""
    conn.execute(
        "select set_config('request.jwt.claims', %s, false)",
        ('{"sub": "%s", "role": "authenticated"}' % auth_user_id,),
    )
    conn.execute("set role authenticated")


def act_as_admin(conn) -> None:
    conn.execute("reset role")
    conn.execute("select set_config('request.jwt.claims', '', false)")


def cleanup_tenant(conn, tenant_id: int, auth_user_ids: list[str] | None = None) -> None:
    conn.execute("delete from public.tenants where id = %s", (tenant_id,))
    for auth_user_id in auth_user_ids or []:
        conn.execute("delete from auth.users where id = %s", (auth_user_id,))
