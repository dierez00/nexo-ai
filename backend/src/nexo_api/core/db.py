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


async def check_database() -> bool:
    """Ping mínimo a la base de datos (`SELECT 1`). Lanza si no hay conexión."""
    async with get_engine().connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True


async def dispose_engine() -> None:
    """Cierra el pool de conexiones. Llamar en el shutdown de la app."""
    await get_engine().dispose()
