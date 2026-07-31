"""Confirmación durable de una ``ActionRequest`` canónica."""

from __future__ import annotations

from nexo_api.core.errors import ProblemException
from nexo_api.repositories import idempotency as idempotency_repo
from nexo_api.repositories import pending_actions
from nexo_api.schemas.action import ConfirmActionRequest
from nexo_api.schemas.auth import UserProfile
from nexo_api.services import idempotency
from nexo_api.services.actions.port import ActionExecutor
from nexo_contracts import ActionResult, ActionStatus


async def confirm_action(
    user: UserProfile,
    action_id: str,
    idempotency_key: str | None,
    body: ConfirmActionRequest,
    executor: ActionExecutor,
) -> ActionResult:
    if not idempotency_key:
        raise ProblemException(
            code="VALIDATION_ERROR",
            title="Falta el header Idempotency-Key",
            detail="Toda escritura requiere el header 'Idempotency-Key'.",
        )
    if not body.consent:
        raise ProblemException(
            code="ACTION_CONFIRMATION_REQUIRED",
            title="Se requiere consentimiento",
            detail="Envía consent=true para confirmar la acción.",
        )

    tenant_id = int(user.tenant_id)
    row = await pending_actions.get(tenant_id, action_id)
    if row is None:
        raise ProblemException(code="RESOURCE_NOT_FOUND", title="Acción pendiente no encontrada")
    pending = pending_actions.request_from(row)
    if pending.expected_version != body.expected_version:
        raise ProblemException(code="VERSION_CONFLICT", title="Versión de acción desactualizada")
    if pending.required_permission not in user.permissions:
        raise ProblemException(
            code="PERMISSION_DENIED",
            title="Permiso insuficiente",
            detail=f"Se requiere el permiso '{pending.required_permission}'.",
        )
    if pending.status is not ActionStatus.PENDING_CONFIRMATION:
        raise ProblemException(code="VERSION_CONFLICT", title="La acción ya fue confirmada")

    operation = f"actions.confirm:{action_id}"
    record, owned = await idempotency.claim(
        tenant_id,
        operation,
        idempotency_key,
        {"consent": body.consent, "expected_version": body.expected_version},
    )
    if not owned:
        result = ActionResult.model_validate(idempotency_repo.response_body(record))
        return result.model_copy(update={"idempotency_replayed": True})

    confirmed = pending.model_copy(
        update={
            "consent": True,
            "idempotency_key": idempotency_key,
            "status": ActionStatus.CONFIRMED,
        }
    )
    try:
        result = await executor.execute(confirmed)
    except Exception as exc:  # noqa: BLE001 - efecto externo indeterminado
        await idempotency_repo.complete(
            int(record["id"]),
            status="unknown",
            response_status=503,
            response_body={"code": "UNKNOWN_OUTCOME", "title": "Resultado indeterminado"},
        )
        raise ProblemException(code="UNKNOWN_OUTCOME", title="Resultado indeterminado") from exc

    if result.action_id != action_id:
        raise RuntimeError("el executor devolvió un resultado para otra acción")
    await pending_actions.complete(tenant_id, action_id, result)
    await idempotency_repo.complete(
        int(record["id"]),
        status="succeeded" if result.status is ActionStatus.SUCCEEDED else "failed",
        response_status=200,
        response_body=result.model_dump(mode="json"),
        resource_id=result.action_id,
    )
    return result
