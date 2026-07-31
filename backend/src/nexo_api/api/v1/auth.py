"""Router de auth: login y perfil del usuario actual."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nexo_api.api.deps import get_current_user, require_role
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import (
    CreateUserRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    UserProfile,
)
from nexo_api.services.auth.login import authenticate, refresh_session
from nexo_api.services.auth.users import create_user

router = APIRouter(prefix="/api/v1", tags=["auth"])
_require_admin = require_role("admin")


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="Login vía Supabase Auth",
    responses=problem_responses(401, 403),
)
async def login(body: LoginRequest) -> LoginResponse:
    return await authenticate(body.email, body.password)


@router.post(
    "/auth/refresh",
    response_model=LoginResponse,
    summary="Renovar sesión vía Supabase Auth",
    responses=problem_responses(401, 403),
)
async def refresh(body: RefreshRequest) -> LoginResponse:
    return await refresh_session(body.refresh_token)


@router.post(
    "/auth/users",
    response_model=UserProfile,
    summary="Crear usuario sin invitación",
    responses=problem_responses(400, 401, 403, 404, 409, 502),
)
async def create_auth_user(
    body: CreateUserRequest,
    admin: UserProfile = Depends(_require_admin),
) -> UserProfile:
    return await create_user(admin, body)


@router.get(
    "/users/me",
    response_model=UserProfile,
    summary="Perfil del usuario actual",
    responses=problem_responses(401, 403),
)
async def users_me(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user
