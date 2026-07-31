"""Esquemas Pydantic de auth (wire: snake_case)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - tipo OAuth, no un secreto


class Institution(BaseModel):
    tenant_id: str
    name: str
    slug: str


class Branch(BaseModel):
    branch_id: str
    code: str
    name: str


class UserProfile(BaseModel):
    user_id: str
    auth_user_id: str
    tenant_id: str
    email: str
    name: str
    role: str
    permissions: list[str]
    # Perfil enriquecido (Core). Defaults para no romper fixtures existentes.
    institution: Institution | None = None
    branch: Branch | None = None
    is_owner: bool = False
    preferences: dict[str, Any] = Field(default_factory=dict)
    # Ciudadano anónimo (sin token). Los servicios no lo asocian a un user_id:
    # sus escrituras (conversación, hold) quedan con `user_id = NULL`.
    is_public: bool = False


class LoginResponse(BaseModel):
    tokens: TokenPair
    profile: UserProfile
