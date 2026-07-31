"""Router de auth: login y perfil del usuario actual."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nexo_api.api.deps import get_current_user
from nexo_api.core.errors import problem_responses
from nexo_api.schemas.auth import LoginRequest, LoginResponse, UserProfile
from nexo_api.services.auth.login import authenticate

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="Login vía Supabase Auth",
    responses=problem_responses(401, 403),
)
async def login(body: LoginRequest) -> LoginResponse:
    return await authenticate(body.email, body.password)


@router.get(
    "/users/me",
    response_model=UserProfile,
    summary="Perfil del usuario actual",
    responses=problem_responses(401, 403),
)
async def users_me(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user
