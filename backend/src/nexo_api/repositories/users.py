"""Lectura del perfil de negocio desde la base (schema de Daher).

Resuelve el `public.users` + rol + permisos efectivos a partir del
`auth_user_id` (el `sub` del JWT de Supabase). El backend conecta con el rol
`postgres` del pooler, que hace bypass de RLS; por eso filtramos explícitamente
por `auth_user_id`.
"""

from __future__ import annotations

from sqlalchemy import text

from nexo_api.core.db import get_sessionmaker
from nexo_api.repositories._base import load_json
from nexo_api.schemas.auth import Branch, Institution, UserProfile

_PROFILE_SQL = text("""
    select
        u.id            as user_id,
        u.auth_user_id  as auth_user_id,
        u.tenant_id     as tenant_id,
        u.email         as email,
        u.name          as name,
        u.is_owner      as is_owner,
        u.metadata      as metadata,
        r.code          as role_code,
        t.name          as tenant_name,
        t.slug          as tenant_slug,
        b.id            as branch_id,
        b.code          as branch_code,
        b.name          as branch_name,
        coalesce(
            array_agg(p.code) filter (where p.code is not null),
            array[]::text[]
        )               as permissions
    from public.users u
    join public.roles r             on r.id = u.role_id
    join public.tenants t           on t.id = u.tenant_id
    left join public.branches b     on b.id = u.branch_id
    left join public.role_permissions rp on rp.role_id = r.id
    left join public.permissions p       on p.id = rp.permission_id
    where u.auth_user_id = :auth_id
      and u.status = 'active'
    group by u.id, r.code, t.name, t.slug, b.id, b.code, b.name
""")


async def load_profile_by_auth_id(auth_id: str) -> UserProfile | None:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        row = (await session.execute(_PROFILE_SQL, {"auth_id": auth_id})).mappings().first()
    if row is None:
        return None
    branch = (
        Branch(
            branch_id=str(row["branch_id"]),
            code=row["branch_code"],
            name=row["branch_name"],
        )
        if row["branch_id"] is not None
        else None
    )
    return UserProfile(
        user_id=str(row["user_id"]),
        auth_user_id=str(row["auth_user_id"]),
        tenant_id=str(row["tenant_id"]),
        email=row["email"],
        name=row["name"],
        role=row["role_code"],
        permissions=list(row["permissions"]),
        institution=Institution(
            tenant_id=str(row["tenant_id"]),
            name=row["tenant_name"],
            slug=row["tenant_slug"],
        ),
        branch=branch,
        is_owner=bool(row["is_owner"]),
        preferences=load_json(row["metadata"]) or {},
    )
