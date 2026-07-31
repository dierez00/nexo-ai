"""Adapter Supabase — cliente async detrás de un puerto.

El backend inyecta `url` y `service_role_key` (desde su config); este paquete
no lee variables de entorno ni secretos. Ver `dani-scope`: los SDKs externos
viven aquí, no en `backend`.
"""

from __future__ import annotations

from nexo_integrations.supabase.client import create_supabase_client

__all__ = ["create_supabase_client"]
