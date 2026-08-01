"""Siembra el demo mínimo para login end-to-end (idempotente, fail-fast).

Crea/asegura:
  - El vínculo del tenant demo con el namespace institucional del corpus.
  - Catálogo de permisos `{modulo}.{read|write}` para los 5 módulos, enlazados al
    rol `admin` (todos) y al rol `citizen` (los de trámite ciudadano).
  - Dos usuarios en Supabase Auth con su fila de negocio en `public.users`:
    la persona administradora y la ciudadana.

Los dos roles no son decorativos: el recorrido ciudadano corre como `citizen`
—que es el rol que la matriz de tools autoriza para escribir una cita— y `/admin`
solo lo abre `admin`. Sembrar únicamente al administrador hacía que el chat no
viera ninguna tool, porque `config/permissions.yaml` no concede nada a ese rol.

Requiere `.env` con SUPABASE_URL, SUPABASE_SECRET_KEY y DATABASE_URL válidos.
Credenciales demo configurables por entorno (SEED_DEMO_EMAIL / SEED_DEMO_PASSWORD).

Uso (desde la raíz del repo):
    uv run python scripts/seed_demo.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import anyio
from nexo_api.core.config import get_settings
from nexo_integrations.supabase import create_supabase_client
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

DEMO_PASSWORD = os.getenv("SEED_DEMO_PASSWORD", "Demo1234!")  # noqa: S105 - demo local
PUBLIC_TENANT_SLUG = os.getenv("PUBLIC_TENANT_SLUG", "gobierno-demo")


@dataclass(frozen=True)
class DemoUser:
    email: str
    name: str
    role_code: str
    is_owner: bool


DEMO_USERS = (
    DemoUser(
        email=os.getenv("SEED_DEMO_EMAIL", "admin@gobierno-demo.mx"),
        name="Administrador Demo",
        role_code="admin",
        is_owner=True,
    ),
    DemoUser(
        email=os.getenv("SEED_CITIZEN_EMAIL", "ciudadano@gobierno-demo.mx"),
        name="Ciudadana Demo",
        role_code="citizen",
        is_owner=False,
    ),
)

# Compatibilidad con quien importaba el nombre anterior.
DEMO_EMAIL = DEMO_USERS[0].email

_PERMISSIONS_SQL = text("""
    insert into public.permissions (code, description, module_id)
    select m.code || '.' || a.act, m.name || ' - ' || a.act, m.id
    from public.modules m
    cross join (values ('read'), ('write')) as a(act)
    on conflict (code) do nothing;
""")

# El corpus documental (`domains/*/sources.yaml`) y la matriz de permisos
# (`config/permissions.yaml`) se publican bajo `inst_demo`. Sin este vínculo el
# retriever filtra por `inst_{id}`, no encuentra ningún documento y el run
# responde «no encontré documentación vigente» sin que nada falle.
_INSTITUTION_REF_SQL = text("""
    update public.tenants
       set metadata = metadata || jsonb_build_object('institution_id', 'inst_demo')
     where slug = :slug and metadata->>'institution_id' is distinct from 'inst_demo';
""")

_ROLE_PERMS_SQL = text("""
    insert into public.role_permissions (role_id, permission_id)
    select r.id, p.id
    from public.roles r
    cross join public.permissions p
    where r.code = 'admin' and r.tenant_id is null
    on conflict do nothing;
""")

# La ciudadanía necesita leer y escribir en los módulos de trámite: sin `.write`
# la API rechaza la confirmación de la acción antes de llegar a la tool.
_CITIZEN_PERMS_SQL = text("""
    insert into public.role_permissions (role_id, permission_id)
    select r.id, p.id
    from public.roles r
    cross join public.permissions p
    join public.modules m on m.id = p.module_id
    where r.code = 'citizen' and r.tenant_id is null
      and m.code in ('vehiculos', 'ayuntamiento_empresas', 'registro_civil', 'salud')
    on conflict do nothing;
""")

_UPSERT_USER_SQL = text("""
    insert into public.users (auth_user_id, tenant_id, role_id, email, name, status, is_owner)
    values (
        cast(:auth_id as uuid),
        (select id from public.tenants where slug = :slug),
        (select id from public.roles where code = :role_code and tenant_id is null),
        :email, :name, 'active', :is_owner
    )
    on conflict (auth_user_id) do update
        set tenant_id = excluded.tenant_id,
            role_id = excluded.role_id,
            name = excluded.name,
            is_owner = excluded.is_owner
    returning id;
""")


async def _ensure_auth_user(url: str, secret_key: str, email: str, password: str) -> str:
    """Crea el usuario en Supabase Auth, o realinea la contraseña del existente.

    Realinear no es cosmético: sin ello el seed es idempotente en la base pero no
    en Auth, y un proyecto donde alguien ya creó el usuario con otra contraseña
    deja el login demo roto sin que nada lo reporte. El reset de datos antes de
    cada demo (y los E2E de Playwright) dependen de que estas credenciales sean
    las documentadas.
    """
    admin = await create_supabase_client(url, secret_key)
    try:
        resp = await admin.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        )
    except Exception as exc:  # noqa: BLE001 - probablemente ya existe; lo buscamos
        print(f"create_user falló ({type(exc).__name__}); buscando usuario existente…")
        for user in await admin.auth.admin.list_users():
            if user.email == email:
                await admin.auth.admin.update_user_by_id(
                    user.id, {"password": password, "email_confirm": True}
                )
                print("usuario existente: contraseña demo realineada")
                return user.id
        raise RuntimeError(f"no se pudo crear ni encontrar el usuario {email}") from exc

    if resp.user is None:
        raise RuntimeError("create_user no devolvió usuario")
    return resp.user.id


async def _print_counts(conn: AsyncConnection) -> None:
    for table in ("permissions", "role_permissions", "users"):
        result = await conn.execute(text(f"select count(*) from public.{table}"))  # noqa: S608
        print(f"  {table}: {result.scalar_one()}")


async def _seed_db(database_url: str, auth_ids: dict[str, str]) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(_INSTITUTION_REF_SQL, {"slug": PUBLIC_TENANT_SLUG})
            await conn.execute(_PERMISSIONS_SQL)
            await conn.execute(_ROLE_PERMS_SQL)
            await conn.execute(_CITIZEN_PERMS_SQL)
            for user in DEMO_USERS:
                user_id = (
                    await conn.execute(
                        _UPSERT_USER_SQL,
                        {
                            "auth_id": auth_ids[user.email],
                            "email": user.email,
                            "name": user.name,
                            "role_code": user.role_code,
                            "is_owner": user.is_owner,
                            "slug": PUBLIC_TENANT_SLUG,
                        },
                    )
                ).scalar_one()
                print(f"public.users id={user_id} {user.email} ({user.role_code})")
        async with engine.connect() as conn:
            await _print_counts(conn)
    finally:
        await engine.dispose()


async def _main() -> None:
    settings = get_settings()
    if not settings.supabase_configured:
        raise SystemExit("Supabase no configurado: revisa SUPABASE_URL/SUPABASE_SECRET_KEY en .env")

    auth_ids: dict[str, str] = {}
    for user in DEMO_USERS:
        auth_ids[user.email] = await _ensure_auth_user(
            settings.supabase_url,
            settings.supabase_secret_key.get_secret_value(),
            user.email,
            DEMO_PASSWORD,
        )
        print(f"auth user {user.email}: {auth_ids[user.email]}")

    await _seed_db(settings.database_url, auth_ids)
    print("\nDEMO LISTO")
    for user in DEMO_USERS:
        print(f"  {user.role_code:>7}: {user.email} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    anyio.run(_main)
