"""Validación de JWT emitidos por Supabase Auth (firma asimétrica ES256).

Ruta A (ver dani-api-contract): Supabase Auth emite los tokens; el backend los
VALIDA con el JWKS público del proyecto. La separación por tenant y los permisos
viven en la base (RLS + role_permissions), no en el token.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from nexo_api.core.config import get_settings


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(get_settings().supabase_jwks_url)


def verify_supabase_jwt(token: str) -> dict[str, Any]:
    """Valida firma, expiración y audiencia. Lanza `jwt.PyJWTError` si es inválido."""
    settings = get_settings()
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    payload: dict[str, Any] = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience=settings.supabase_jwt_aud,
        options={"require": ["exp", "sub"]},
    )
    return payload
