"""Router de auth: login y perfil del usuario actual."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nexo_api.api.deps import get_current_user
from nexo_api.schemas.auth import LoginRequest, LoginResponse, UserProfile
from nexo_api.services.auth.login import authenticate

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    return await authenticate(body.email, body.password)


@router.get("/users/me", response_model=UserProfile)
async def users_me(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user
