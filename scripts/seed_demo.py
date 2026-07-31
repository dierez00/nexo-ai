"""Siembra el demo mínimo para login end-to-end (idempotente, fail-fast).

Crea/asegura:
  - Catálogo de permisos `{modulo}.{read|write}` para los 5 módulos + los enlaza
    al rol `admin` (role_permissions).
  - Un usuario en Supabase Auth y su fila de negocio en `public.users`
    (tenant 1, rol admin).

Requiere `.env` con SUPABASE_URL, SUPABASE_SECRET_KEY y DATABASE_URL válidos.
Credenciales demo configurables por entorno (SEED_DEMO_EMAIL / SEED_DEMO_PASSWORD).

Uso (desde la raíz del repo):
    uv run python scripts/seed_demo.py
"""

from __future__ import annotations

import os

import anyio
from nexo_api.core.config import get_settings
from nexo_integrations.supabase import create_supabase_client
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

DEMO_EMAIL = os.getenv("SEED_DEMO_EMAIL", "admin@gobierno-demo.mx")
DEMO_PASSWORD = os.getenv("SEED_DEMO_PASSWORD", "Demo1234!")  # noqa: S105 - demo local

_PERMISSIONS_SQL = text("""
    insert into public.permissions (code, description, module_id)
    select m.code || '.' || a.act, m.name || ' - ' || a.act, m.id
    from public.modules m
    cross join (values ('read'), ('write')) as a(act)
    on conflict (code) do nothing;
""")

_ROLE_PERMS_SQL = text("""
    insert into public.role_permissions (role_id, permission_id)
    select r.id, p.id
    from public.roles r
    cross join public.permissions p
    where r.code = 'admin' and r.tenant_id is null
    on conflict do nothing;
""")

_UPSERT_USER_SQL = text("""
    insert into public.users (auth_user_id, tenant_id, role_id, email, name, status, is_owner)
    values (
        cast(:auth_id as uuid), 1,
        (select id from public.roles where code = 'admin' and tenant_id is null),
        :email, 'Administrador Demo', 'active', true
    )
    on conflict (auth_user_id) do update
        set tenant_id = excluded.tenant_id, role_id = excluded.role_id
    returning id;
""")


async def _ensure_auth_user(url: str, secret_key: str, email: str, password: str) -> str:
    """Crea el usuario en Supabase Auth o devuelve el existente."""
    admin = await create_supabase_client(url, secret_key)
    try:
        resp = await admin.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        )
    except Exception as exc:  # noqa: BLE001 - probablemente ya existe; lo buscamos
        print(f"create_user falló ({type(exc).__name__}); buscando usuario existente…")
        for user in await admin.auth.admin.list_users():
            if user.email == email:
                return user.id
        raise RuntimeError(f"no se pudo crear ni encontrar el usuario {email}") from exc

    if resp.user is None:
        raise RuntimeError("create_user no devolvió usuario")
    return resp.user.id


async def _print_counts(conn: AsyncConnection) -> None:
    for table in ("permissions", "role_permissions", "users"):
        result = await conn.execute(text(f"select count(*) from public.{table}"))  # noqa: S608
        print(f"  {table}: {result.scalar_one()}")


async def _seed_db(database_url: str, auth_id: str, email: str) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(_PERMISSIONS_SQL)
            await conn.execute(_ROLE_PERMS_SQL)
            user_id = (
                await conn.execute(_UPSERT_USER_SQL, {"auth_id": auth_id, "email": email})
            ).scalar_one()
        print(f"public.users id: {user_id}")
        async with engine.connect() as conn:
            await _print_counts(conn)
    finally:
        await engine.dispose()


async def _main() -> None:
    settings = get_settings()
    if not settings.supabase_configured:
        raise SystemExit("Supabase no configurado: revisa SUPABASE_URL/SUPABASE_SECRET_KEY en .env")

    auth_id = await _ensure_auth_user(
        settings.supabase_url,
        settings.supabase_secret_key.get_secret_value(),
        DEMO_EMAIL,
        DEMO_PASSWORD,
    )
    print(f"auth user: {auth_id}")
    await _seed_db(settings.database_url, auth_id, DEMO_EMAIL)
    print(f"\nDEMO LISTO -> {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    anyio.run(_main)
