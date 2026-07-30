"""Tests del factory de Supabase (sin red: solo validación de credenciales)."""

from __future__ import annotations

import pytest
from nexo_integrations.supabase import create_supabase_client


@pytest.mark.parametrize(
    ("url", "key"),
    [
        ("", "some-key"),
        ("https://x.supabase.co", ""),
        ("", ""),
    ],
)
async def test_missing_credentials_raise(url: str, key: str) -> None:
    with pytest.raises(ValueError, match="requeridos"):
        await create_supabase_client(url, key)
