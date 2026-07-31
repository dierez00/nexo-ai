"""Dependencias FastAPI para auth: usuario actual y RBAC.

`get_current_user` valida el JWT de Supabase (JWKS) y resuelve el perfil de
negocio desde la base. `require_permission` aplica permisos server-side
(§13: permisos siempre en el servidor).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import jwt
from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nexo_api.core.errors import ProblemException
from nexo_api.core.security import verify_supabase_jwt
from nexo_api.repositories.users import load_profile_by_auth_id
from nexo_api.schemas.auth import UserProfile
from nexo_api.services.actions import ActionExecutor, FakeActionExecutor
from nexo_api.services.orchestration import FakeOrchestrator, Orchestrator


def get_orchestrator() -> Orchestrator:
    """Provee el orquestador. Hoy fake; se cambia por el real de Diego sin tocar routers."""
    return FakeOrchestrator()


def get_action_executor() -> ActionExecutor:
    """Provee el ejecutor transaccional. Hoy fake; luego la tool MCP real."""
    return FakeActionExecutor()


_bearer = HTTPBearer(auto_error=False)


async def _profile_from_token(token: str) -> UserProfile:
    """Valida el JWT de Supabase y resuelve el perfil. Compartido por header y SSE."""
    try:
        payload = verify_supabase_jwt(token)
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
    return await _profile_from_token(credentials.credentials)


async def get_current_user_sse(
    request: Request,
    access_token: str | None = Query(default=None),
) -> UserProfile:
    """Auth para SSE: el `EventSource` del browser no manda header `Authorization`,
    así que acepta el token por query param `?access_token=` o por el header."""
    token = access_token
    if token is None:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header.removeprefix("Bearer ")
    if not token:
        raise ProblemException(
            status=401,
            code="AUTHENTICATION_REQUIRED",
            title="Falta el token de autenticación",
            detail="Usa '?access_token=<token>' o el header 'Authorization: Bearer <token>'.",
        )
    return await _profile_from_token(token)


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
