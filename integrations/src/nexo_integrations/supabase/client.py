"""Fábrica del cliente async de Supabase.

Uso desde backend:
    from nexo_integrations.supabase import create_supabase_client
    client = await create_supabase_client(settings.supabase_url, secret_key)

Se usa la SECRET key (bypassa RLS) → SOLO backend/agentes, nunca el frontend.
Las credenciales se reciben como parámetros; este módulo no toca config ni
entorno.
"""

from __future__ import annotations

from supabase import AsyncClient, create_async_client


async def create_supabase_client(url: str, secret_key: str) -> AsyncClient:
    """Construye un `AsyncClient` de Supabase.

    Lanza `ValueError` si falta alguna credencial, para fallar temprano y con
    un error normalizado en vez de un fallo opaco del SDK más adelante.
    """
    if not url or not secret_key:
        raise ValueError("supabase_url y secret_key son requeridos")
    return await create_async_client(url, secret_key)
