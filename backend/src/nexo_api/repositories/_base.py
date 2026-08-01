"""Utilidades compartidas de repositorios (Unit of Work simple)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from nexo_api.core.db import get_append_sessionmaker, get_sessionmaker


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


async def append_once(
    statement: Any,  # noqa: ANN401 - `TextClause` de SQLAlchemy
    parameters: dict[str, Any],
) -> Any:  # noqa: ANN401 - `Result` de SQLAlchemy
    """Ejecuta una escritura append-only de una sola sentencia, en AUTOCOMMIT.

    Reintenta una vez si el pool entregó una conexión que el servidor ya había
    cerrado. Es la contrapartida de renunciar a `pool_pre_ping` en este camino:
    la misma garantía, pero pagada solo cuando de verdad ocurre.
    """
    for attempt in (1, 2):
        try:
            async with get_append_sessionmaker()() as session:
                return await session.execute(statement, parameters)
        except DBAPIError as exc:
            if attempt == 2 or not exc.connection_invalidated:
                raise
    raise AssertionError("inalcanzable")  # pragma: no cover
