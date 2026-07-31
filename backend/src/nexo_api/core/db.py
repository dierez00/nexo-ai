"""Motor y sesiones async de SQLAlchemy.

Dani expone el `AsyncEngine` y la fábrica de sesiones; los modelos, migraciones
y repositorios son responsabilidad de Daher (carpeta `database`). Aquí solo vive
la infraestructura de conexión y el chequeo de salud usado por `/health/ready`.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nexo_api.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Devuelve el `AsyncEngine` singleton (cacheado)."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Fábrica de sesiones async ligada al engine singleton."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


@lru_cache(maxsize=1)
def get_append_engine() -> AsyncEngine:
    """Engine para escrituras append-only de una sola sentencia (eventos del run).

    Contra una base remota, envolver un `insert` en una transacción explícita
    cuesta tres idas y vuelta (BEGIN, INSERT, COMMIT) más el ROLLBACK de
    devolución al pool, y `pool_pre_ping` añade una cuarta. Medido contra el
    pooler de Supabase eso son ~1.1 s por evento; un run emite decenas, así que
    la observabilidad terminaba consumiendo el presupuesto del propio run.

    En AUTOCOMMIT y sin pre-ping el mismo `insert` cuesta una ida y vuelta
    (~0.11 s). Se prescinde del pre-ping porque su garantía —detectar una
    conexión que el pooler cerró— la da igual de bien un reintento en el punto de
    escritura, y ese reintento no cuesta nada cuando la conexión está viva.
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=False,
        pool_size=5,
        max_overflow=5,
        isolation_level="AUTOCOMMIT",
    )


@lru_cache(maxsize=1)
def get_append_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Fábrica de sesiones ligada al engine de escrituras append-only."""
    return async_sessionmaker(get_append_engine(), expire_on_commit=False)


async def check_database() -> bool:
    """Ping mínimo a la base de datos (`SELECT 1`). Lanza si no hay conexión."""
    async with get_engine().connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True


async def dispose_engine() -> None:
    """Cierra los pools de conexiones. Llamar en el shutdown de la app."""
    await get_engine().dispose()
    await get_append_engine().dispose()
