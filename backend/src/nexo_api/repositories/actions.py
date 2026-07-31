"""Repositorio de actions (idempotencia por idempotency_key UNIQUE)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, read_session, uow

_COLS = "id, idempotency_key, action_name, status, result_folio, result_payload, created_at"


async def find_by_idempotency_key(tenant_id: int, key: str) -> RowMapping | None:
    sql = text(
        f"select {_COLS} from public.actions "
        "where idempotency_key = :key and tenant_id = :tenant_id"
    )
    async with read_session() as session:
        result = await session.execute(sql, {"key": key, "tenant_id": tenant_id})
        return result.mappings().first()


async def create(
    tenant_id: int,
    user_id: int | None,
    idempotency_key: str,
    action_name: str,
    payload: dict[str, Any],
    status: str,
    result_folio: str | None,
    result_payload: dict[str, Any],
) -> RowMapping:
    sql = text(f"""
        insert into public.actions
            (tenant_id, user_id, idempotency_key, action_name, payload,
             status, result_folio, result_payload)
        values
            (:tenant_id, :user_id, :idempotency_key, :action_name, cast(:payload as jsonb),
             :status, :result_folio, cast(:result_payload as jsonb))
        returning {_COLS}
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "idempotency_key": idempotency_key,
                "action_name": action_name,
                "payload": dump_json(payload),
                "status": status,
                "result_folio": result_folio,
                "result_payload": dump_json(result_payload),
            },
        )
        return result.mappings().one()
