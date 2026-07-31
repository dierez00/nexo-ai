"""Utilidades compartidas de repositorios (Unit of Work simple)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from nexo_api.core.db import get_sessionmaker


def load_json(value: Any) -> Any:  # noqa: ANN401 - JSON arbitrario de una columna jsonb
    """asyncpg puede devolver jsonb como str; normaliza a objeto Python."""
    return json.loads(value) if isinstance(value, str) else value


def dump_json(value: Any) -> str:  # noqa: ANN401 - acepta cualquier valor serializable
    """Serializa a JSON para bindear a columnas jsonb con `cast(:x as jsonb)`."""
    return json.dumps(value, default=str)


@asynccontextmanager
async def uow() -> AsyncIterator[AsyncSession]:
    """Unit of Work: commit al salir sin error, rollback si algo falla."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def read_session() -> AsyncIterator[AsyncSession]:
    """Sesión de solo lectura (sin commit)."""
    async with get_sessionmaker()() as session:
        yield session
