"""Caso de uso de login: proxy a Supabase Auth + carga de perfil.

El backend delega la verificación de credenciales en Supabase Auth
(`sign_in_with_password`, contexto anónimo con la publishable key) y devuelve
la sesión de Supabase junto con el perfil de negocio resuelto desde la base.

Un fallo de **transporte** (timeout, DNS, proveedor caído) no es un fallo de
credenciales: mapear ambos a 401 le dice a quien presenta la demo que su
contraseña está mal cuando en realidad se cayó la red. Se distinguen para que el
frontend pueda ofrecer «reintentar» en vez de «revisa tus datos».
"""

from __future__ import annotations

import httpx
from nexo_integrations.supabase import create_supabase_client
from nexo_observability.logging import get_logger

from nexo_api.core.config import get_settings
from nexo_api.core.errors import ProblemException
from nexo_api.repositories.users import load_profile_by_auth_id
from nexo_api.schemas.auth import LoginResponse, TokenPair, UserProfile

log = get_logger(__name__)


def _transport_failure(exc: Exception, operation: str) -> ProblemException:
    """503 reintentable cuando el proveedor de identidad no respondió."""
    log.warning("auth.provider_unreachable", operation=operation, error=type(exc).__name__)
    # El HTTP y el `retryable` los deriva `ProblemException` de la tabla de
    # contratos a partir del código; aquí solo se elige el código correcto.
    return ProblemException(
        code="PROVIDER_ERROR",
        title="El proveedor de identidad no responde",
        detail="No pudimos contactar a Supabase Auth. Reintenta en unos segundos.",
    )


async def _profile_for(auth_user_id: str) -> UserProfile:
    profile = await load_profile_by_auth_id(auth_user_id)
    if profile is None:
        raise ProblemException(
            status=403,
            code="PERMISSION_DENIED",
            title="Usuario sin perfil aprovisionado",
            detail="El usuario existe en Supabase Auth pero no tiene registro en public.users.",
        )
    return profile


async def authenticate(email: str, password: str) -> LoginResponse:
    settings = get_settings()
    client = await create_supabase_client(settings.supabase_url, settings.supabase_publishable_key)

    try:
        result = await client.auth.sign_in_with_password({"email": email, "password": password})
    except httpx.HTTPError as exc:
        raise _transport_failure(exc, "sign_in_with_password") from exc
    except Exception as exc:  # noqa: BLE001 - credenciales rechazadas por el proveedor
        log.info("auth.sign_in_rejected", error=type(exc).__name__)
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

    tokens = TokenPair(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )
    return LoginResponse(tokens=tokens, profile=await _profile_for(user.id))


async def refresh_session(refresh_token: str) -> LoginResponse:
    settings = get_settings()
    client = await create_supabase_client(settings.supabase_url, settings.supabase_publishable_key)

    try:
        result = await client.auth.refresh_session(refresh_token)
    except httpx.HTTPError as exc:
        raise _transport_failure(exc, "refresh_session") from exc
    except Exception as exc:  # noqa: BLE001 - refresh rechazado por el proveedor
        log.info("auth.refresh_rejected", error=type(exc).__name__)
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Sesión expirada",
            detail="Vuelve a iniciar sesión.",
        ) from exc

    session = result.session
    user = result.user
    if session is None or user is None:
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Sesión expirada",
            detail="Vuelve a iniciar sesión.",
        )

    tokens = TokenPair(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )
    return LoginResponse(tokens=tokens, profile=await _profile_for(user.id))
