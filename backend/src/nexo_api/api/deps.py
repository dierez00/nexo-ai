"""Dependencias FastAPI para auth: usuario actual y RBAC.

`get_current_user` valida el JWT de Supabase (JWKS) y resuelve el perfil de
negocio desde la base. `require_permission` aplica permisos server-side
(§13: permisos siempre en el servidor).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nexo_api.auth.repository import load_profile_by_auth_id
from nexo_api.auth.schemas import UserProfile
from nexo_api.auth.security import verify_supabase_jwt
from nexo_api.errors import ProblemException

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserProfile:
    if credentials is None:
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Falta el token de autenticación",
            detail="Incluye el header 'Authorization: Bearer <token>'.",
        )
    try:
        payload = verify_supabase_jwt(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Token inválido o expirado",
            detail=str(exc),
        ) from exc

    profile = await load_profile_by_auth_id(payload["sub"])
    if profile is None:
        raise ProblemException(
            status=403,
            code="PERMISSION_DENIED",
            title="Usuario sin perfil aprovisionado",
            detail="El token es válido pero no hay registro en public.users.",
        )
    return profile


def require_permission(permission: str) -> Callable[[UserProfile], Awaitable[UserProfile]]:
    async def _checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if permission not in user.permissions:
            raise ProblemException(
                status=403,
                code="PERMISSION_DENIED",
                title="Permiso insuficiente",
                detail=f"Se requiere el permiso '{permission}'.",
            )
        return user

    return _checker
