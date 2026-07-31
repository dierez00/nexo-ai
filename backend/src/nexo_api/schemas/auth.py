"""Esquemas Pydantic de auth (wire: snake_case)."""

from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - tipo OAuth, no un secreto


class UserProfile(BaseModel):
    user_id: str
    auth_user_id: str
    tenant_id: str
    email: str
    name: str
    role: str
    permissions: list[str]


class LoginResponse(BaseModel):
    tokens: TokenPair
    profile: UserProfile
