"""Administración de usuarios vía Supabase Auth sin invitación."""

from __future__ import annotations

from typing import Any, cast

from nexo_integrations.supabase import create_supabase_client
from nexo_observability.logging import get_logger

from nexo_api.core.config import get_settings
from nexo_api.core.errors import ProblemException
from nexo_api.repositories.users import load_profile_by_auth_id, provision_business_user
from nexo_api.schemas.auth import CreateUserRequest, UserProfile

log = get_logger(__name__)


async def create_user(admin: UserProfile, body: CreateUserRequest) -> UserProfile:
    settings = get_settings()
    client = await create_supabase_client(
        settings.supabase_url,
        settings.supabase_secret_key.get_secret_value(),
    )

    auth_user_id: str | None = None
    try:
        result = await client.auth.admin.create_user(
            cast(
                Any,
                {
                    "email": body.email,
                    "password": body.password,
                    "email_confirm": body.email_confirm,
                    "user_metadata": {"full_name": body.name},
                },
            )
        )
        auth_user_id = str(result.user.id)
    except Exception as exc:  # noqa: BLE001 - el SDK normaliza distintos errores
        raise ProblemException(
            code="PROVIDER_ERROR",
            title="No pudimos crear el usuario en Supabase Auth",
            detail="Revisa las credenciales de Supabase o si el email ya existe.",
        ) from exc

    try:
        await provision_business_user(
            auth_user_id=auth_user_id,
            tenant_id=int(admin.tenant_id),
            email=body.email,
            name=body.name,
            role_code=body.role_code,
            branch_code=body.branch_code,
            is_owner=body.is_owner,
            metadata=body.metadata,
        )
    except Exception:
        try:
            await client.auth.admin.delete_user(auth_user_id)
        except Exception as cleanup_exc:  # noqa: BLE001 - best effort compensatorio
            log.warning(
                "auth_user_cleanup_failed",
                auth_user_id=auth_user_id,
                error=str(cleanup_exc),
            )
        raise

    profile = await load_profile_by_auth_id(auth_user_id)
    if profile is None:
        raise ProblemException(
            code="PROVIDER_ERROR",
            title="Usuario creado sin perfil legible",
            detail="Supabase Auth creó el usuario, pero public.users no pudo resolverse.",
        )
    return profile
