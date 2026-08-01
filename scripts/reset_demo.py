"""Devuelve el tenant demo a su estado inicial (idempotente).

Borra lo que produce una demostración —conversaciones, runs, eventos, acciones
confirmadas, citas y el ledger de idempotencia— y conserva lo que la sostiene:
tenant, sucursales, módulos, roles, permisos y usuarios.

Existe porque la segunda pasada de la demo no es como la primera: la cita del
recorrido vehicular ocupa el horario 2026-08-03 09:00, y el constraint que impide
solapamientos —el mismo que demuestra el manejo de conflictos— rechaza la
siguiente reserva del mismo hueco. Sin reset, la demo solo funciona una vez.

Uso (desde la raíz del repo):
    uv run python scripts/reset_demo.py
"""

from __future__ import annotations

import os

import anyio
from nexo_api.core.config import get_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

PUBLIC_TENANT_SLUG = os.getenv("PUBLIC_TENANT_SLUG", "gobierno-demo")

_TENANT_ID_SQL = text("select id from public.tenants where slug = :slug")

# El orden respeta las llaves foráneas: los eventos y las acciones cuelgan de los
# runs, y los runs de las conversaciones. `run_events` cae por cascada al borrar
# el run, pero se borra explícitamente para que el script no dependa de ello.
_DELETIONS: tuple[tuple[str, str], ...] = (
    (
        "run_events",
        """delete from public.run_events
           where run_id in (select id from public.runs where tenant_id = :tenant_id)""",
    ),
    ("pending_actions", "delete from public.pending_actions where tenant_id = :tenant_id"),
    ("runs", "delete from public.runs where tenant_id = :tenant_id"),
    (
        "messages",
        """delete from public.messages
           where conversation_id in
             (select id from public.conversations where tenant_id = :tenant_id)""",
    ),
    ("conversations", "delete from public.conversations where tenant_id = :tenant_id"),
    ("appointments", "delete from public.appointments where tenant_id = :tenant_id"),
    ("idempotency_records", "delete from public.idempotency_records where tenant_id = :tenant_id"),
)


async def _reset(conn: AsyncConnection, tenant_id: int) -> None:
    for label, statement in _DELETIONS:
        result = await conn.execute(text(statement), {"tenant_id": tenant_id})
        print(f"  {label}: {result.rowcount} fila(s) borrada(s)")


async def _main() -> None:
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.begin() as conn:
            tenant_id = (
                await conn.execute(_TENANT_ID_SQL, {"slug": PUBLIC_TENANT_SLUG})
            ).scalar_one_or_none()
            if tenant_id is None:
                raise SystemExit(f"no existe el tenant '{PUBLIC_TENANT_SLUG}'")
            print(f"reiniciando tenant '{PUBLIC_TENANT_SLUG}' (id={tenant_id})")
            await _reset(conn, int(tenant_id))
    finally:
        await engine.dispose()
    print("\nDEMO REINICIADA — usuarios, permisos y catálogos intactos")


if __name__ == "__main__":
    anyio.run(_main)
