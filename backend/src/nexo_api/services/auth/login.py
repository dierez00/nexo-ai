"""Caso de uso de login: proxy a Supabase Auth + carga de perfil.

El backend delega la verificación de credenciales en Supabase Auth
(`sign_in_with_password`, contexto anónimo con la publishable key) y devuelve
la sesión de Supabase junto con el perfil de negocio resuelto desde la base.
"""

from __future__ import annotations

from nexo_integrations.supabase import create_supabase_client

from nexo_api.auth.repository import load_profile_by_auth_id
from nexo_api.auth.schemas import LoginResponse, TokenPair
from nexo_api.config import get_settings
from nexo_api.errors import ProblemException


async def authenticate(email: str, password: str) -> LoginResponse:
    settings = get_settings()
    client = await create_supabase_client(settings.supabase_url, settings.supabase_publishable_key)

    try:
        result = await client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:  # noqa: BLE001 - normalizamos cualquier fallo de auth
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Credenciales inválidas",
            detail="El email o la contraseña no coinciden.",
        ) from exc

    session = result.session
    user = result.user
    if session is None or user is None:
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Credenciales inválidas",
        )

    profile = await load_profile_by_auth_id(user.id)
    if profile is None:
        raise ProblemException(
            status=403,
            code="PERMISSION_DENIED",
            title="Usuario sin perfil aprovisionado",
            detail="El usuario existe en Supabase Auth pero no tiene registro en public.users.",
        )

    tokens = TokenPair(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )
    return LoginResponse(tokens=tokens, profile=profile)
