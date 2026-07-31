"""Almacén durable de acciones canónicas propuestas por la orquestación."""

from __future__ import annotations

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, load_json, read_session, uow
from nexo_contracts import ActionRequest, ActionResult


async def create(tenant_id: int, action: ActionRequest) -> None:
    sql = text("""
        insert into public.pending_actions (action_id, tenant_id, run_id, request, status)
        values (:action_id, :tenant_id, :run_id, cast(:request as jsonb), :status)
        on conflict (action_id) do nothing
    """)
    async with uow() as session:
        await session.execute(
            sql,
            {
                "action_id": action.action_id,
                "tenant_id": tenant_id,
                "run_id": int(str(action.run_id).removeprefix("run_")),
                "request": dump_json(action.model_dump(mode="json")),
                "status": action.status.value,
            },
        )


async def get(tenant_id: int, action_id: str) -> RowMapping | None:
    async with read_session() as session:
        result = await session.execute(
            text("""
                select action_id, request, status, result
                from public.pending_actions
                where tenant_id = :tenant_id and action_id = :action_id
            """),
            {"tenant_id": tenant_id, "action_id": action_id},
        )
        return result.mappings().first()


async def owner_context(tenant_id: int, action_id: str) -> RowMapping | None:
    """Traza del run y usuario dueño de la acción, para validar pertenencia.

    Une la acción con su run y la conversación del run: el `user_id` de la
    conversación es quien puede confirmar. `trace_id` se propaga a la invocación
    de la tool para correlacionar la auditoría. Devuelve ``None`` si la acción no
    apunta a un run existente del tenant.
    """
    sql = text("""
        select r.trace_id as trace_id, c.user_id as owner_user_id
        from public.pending_actions pa
        join public.runs r on r.id = pa.run_id and r.tenant_id = pa.tenant_id
        left join public.conversations c on c.id = r.conversation_id
        where pa.action_id = :action_id and pa.tenant_id = :tenant_id
    """)
    async with read_session() as session:
        result = await session.execute(sql, {"tenant_id": tenant_id, "action_id": action_id})
        return result.mappings().first()


async def complete(tenant_id: int, action_id: str, result: ActionResult) -> None:
    async with uow() as session:
        await session.execute(
            text("""
                update public.pending_actions
                set status = :status, result = cast(:result as jsonb), updated_at = now()
                where tenant_id = :tenant_id and action_id = :action_id
            """),
            {
                "tenant_id": tenant_id,
                "action_id": action_id,
                "status": result.status.value,
                "result": dump_json(result.model_dump(mode="json")),
            },
        )


def request_from(row: RowMapping) -> ActionRequest:
    return ActionRequest.model_validate(load_json(row["request"]))
