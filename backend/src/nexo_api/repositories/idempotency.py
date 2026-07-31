"""Ledger transaccional para idempotencia de escrituras HTTP.

La reserva se confirma antes de ejecutar cualquier efecto. El registro es
independiente de `actions` y `appointments`, para que futuras escrituras usen
la misma garant\u00eda sin duplicar l\u00f3gica.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, load_json, read_session, uow

_COLS = "id, request_hash, status, response_status, response_body, resource_id, created_at"


async def claim(
    tenant_id: int, operation: str, idempotency_key: str, request_hash: str
) -> tuple[RowMapping, bool]:
    """Reserva una clave o devuelve su estado ya existente.

    El `insert ... on conflict` hace que solo un request sea propietario de la
    ejecuci\u00f3n, incluso con varias instancias de la API.
    """
    sql = text(f"""
        insert into public.idempotency_records
            (tenant_id, operation, idempotency_key, request_hash, status)
        values (:tenant_id, :operation, :key, :request_hash, 'processing')
        on conflict (tenant_id, operation, idempotency_key) do nothing
        returning {_COLS}
    """)
    params = {
        "tenant_id": tenant_id,
        "operation": operation,
        "key": idempotency_key,
        "request_hash": request_hash,
    }
    async with uow() as session:
        inserted = (await session.execute(sql, params)).mappings().first()
    if inserted is not None:
        return inserted, True

    existing = await get(tenant_id, operation, idempotency_key)
    if existing is None:  # defensa ante una eliminaci\u00f3n manual concurrente
        raise RuntimeError("la reserva de idempotencia desapareci\u00f3")
    return existing, False


async def get(tenant_id: int, operation: str, idempotency_key: str) -> RowMapping | None:
    sql = text(f"""
        select {_COLS} from public.idempotency_records
        where tenant_id = :tenant_id and operation = :operation and idempotency_key = :key
    """)
    async with read_session() as session:
        return (
            (
                await session.execute(
                    sql, {"tenant_id": tenant_id, "operation": operation, "key": idempotency_key}
                )
            )
            .mappings()
            .first()
        )


async def complete(
    record_id: int,
    *,
    status: str,
    response_status: int,
    response_body: dict[str, Any],
    resource_id: str | None = None,
) -> None:
    sql = text("""
        update public.idempotency_records
        set status = :status, response_status = :response_status,
            response_body = cast(:response_body as jsonb), resource_id = :resource_id,
            updated_at = now()
        where id = :id
    """)
    async with uow() as session:
        await session.execute(
            sql,
            {
                "id": record_id,
                "status": status,
                "response_status": response_status,
                "response_body": dump_json(response_body),
                "resource_id": resource_id,
            },
        )


async def mark_stale_processing_unknown(ttl_seconds: int) -> int:
    """Evita que un reinicio deje una clave en ejecuci\u00f3n indefinidamente."""
    threshold = datetime.now(UTC) - timedelta(seconds=ttl_seconds)
    sql = text("""
        update public.idempotency_records
        set status = 'unknown', response_status = 409,
            response_body = cast(:body as jsonb), updated_at = now()
        where status = 'processing' and created_at < :threshold
    """)
    body = {
        "code": "UNKNOWN_OUTCOME",
        "title": "Resultado de escritura indeterminado",
        "detail": (
            "La ejecuci\u00f3n anterior no termin\u00f3 de forma verificable; "
            "no se reintenta autom\u00e1ticamente."
        ),
    }
    async with uow() as session:
        await session.execute(sql, {"threshold": threshold, "body": dump_json(body)})
    return 0


def response_body(row: RowMapping) -> dict[str, Any]:
    value = load_json(row["response_body"])
    return value if isinstance(value, dict) else {}
