"""Caso de uso: confirmar una acción (consentimiento + idempotencia + RBAC)."""

from __future__ import annotations

from sqlalchemy import RowMapping
from sqlalchemy.exc import IntegrityError

from nexo_api.core import ids
from nexo_api.core.errors import ProblemException
from nexo_api.repositories import actions as actions_repo
from nexo_api.repositories._base import load_json
from nexo_api.schemas.action import ActionResult, ConfirmActionRequest
from nexo_api.schemas.auth import UserProfile
from nexo_api.services.actions.port import ActionExecutor


def _to_result(row: RowMapping) -> ActionResult:
    return ActionResult(
        action_id=ids.encode(ids.ACTION, row["id"]),
        idempotency_key=row["idempotency_key"],
        action_name=row["action_name"],
        status=row["status"],
        folio=row["result_folio"],
        result=load_json(row["result_payload"]) or {},
        created_at=row["created_at"],
    )


def _required_permission(action_name: str) -> str | None:
    """Deriva el permiso `{modulo}.write` del nombre de la acción (ej. vehiculos.reservar_cita)."""
    module = action_name.split(".", 1)[0]
    return f"{module}.write" if module else None


async def confirm_action(
    user: UserProfile,
    action_id: str,
    idempotency_key: str | None,
    body: ConfirmActionRequest,
    executor: ActionExecutor,
) -> ActionResult:
    if not idempotency_key:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            title="Falta el header Idempotency-Key",
            detail="Toda escritura requiere el header 'Idempotency-Key'.",
        )
    if not body.consent:
        raise ProblemException(
            status=422,
            code="ACTION_CONFIRMATION_REQUIRED",
            title="Se requiere consentimiento",
            detail="Envía consent=true para confirmar la acción.",
        )

    required = _required_permission(action_id)
    if required and required not in user.permissions:
        raise ProblemException(
            status=403,
            code="PERMISSION_DENIED",
            title="Permiso insuficiente",
            detail=f"Se requiere el permiso '{required}'.",
        )

    tenant_id = int(user.tenant_id)

    # Replay: si la key ya existe, devuelve el MISMO resultado sin segunda escritura (§13).
    existing = await actions_repo.find_by_idempotency_key(tenant_id, idempotency_key)
    if existing is not None:
        return _to_result(existing)

    execution = await executor.execute(action_id, body.input, tenant_id)
    try:
        row = await actions_repo.create(
            tenant_id=tenant_id,
            user_id=int(user.user_id),
            idempotency_key=idempotency_key,
            action_name=action_id,
            payload=body.input,
            status=execution.status,
            result_folio=execution.folio,
            result_payload=execution.result_payload,
        )
    except IntegrityError as exc:
        # Carrera: otro request insertó la misma key entre el check y el insert.
        again = await actions_repo.find_by_idempotency_key(tenant_id, idempotency_key)
        if again is not None:
            return _to_result(again)
        raise ProblemException(
            status=409,
            code="VERSION_CONFLICT",
            title="Idempotency-Key en uso",
            detail="La clave de idempotencia ya está registrada.",
        ) from exc

    return _to_result(row)
