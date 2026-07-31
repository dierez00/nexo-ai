"""Confirmación durable de una ``ActionRequest`` canónica."""

from __future__ import annotations

from nexo_api.core import ids
from nexo_api.core.errors import ProblemException
from nexo_api.repositories import idempotency as idempotency_repo
from nexo_api.repositories import pending_actions
from nexo_api.repositories import runs as runs_repo
from nexo_api.schemas.action import ConfirmActionRequest
from nexo_api.schemas.auth import UserProfile
from nexo_api.services import idempotency
from nexo_api.services.actions.port import ActionExecutor
from nexo_contracts import ActionResult, ActionStatus, RunStatus, ToolPermissionContext

_RUN_STATUS_BY_ACTION: dict[ActionStatus, RunStatus] = {
    ActionStatus.SUCCEEDED: RunStatus.SUCCEEDED,
    ActionStatus.PARTIAL: RunStatus.PARTIAL,
    ActionStatus.FAILED: RunStatus.FAILED,
}


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

    # La acción debe pertenecer a un run real del tenant y a esta persona: sin
    # esto, conocer un action_id bastaría para confirmar la escritura de otro.
    context = await pending_actions.owner_context(tenant_id, action_id)
    if context is None:
        raise ProblemException(
            code="RESOURCE_NOT_FOUND", title="El run de la acción no existe"
        )
    owner_user_id = context["owner_user_id"]
    if owner_user_id is not None and int(owner_user_id) != int(user.user_id):
        raise ProblemException(
            code="PERMISSION_DENIED",
            title="La acción no pertenece al usuario",
            detail="Solo quien inició el run puede confirmar su acción.",
        )
    trace_id = str(context["trace_id"])
    identity = ToolPermissionContext(
        user_id=ids.encode(ids.USER, int(user.user_id)),
        institution_id=ids.encode(ids.INSTITUTION, int(user.tenant_id)),
        roles=[user.role],
        permissions=user.permissions,
    )

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
        result = await executor.execute(confirmed, identity=identity, trace_id=trace_id)
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
    # La confirmación no reanuda el grafo: cierra el run aquí para que `GET /runs`
    # y un SSE reabierto dejen de mostrar `waiting_confirmation`.
    run_status = _RUN_STATUS_BY_ACTION.get(result.status, RunStatus.PARTIAL)
    await runs_repo.set_status(tenant_id, ids.decode(ids.RUN, pending.run_id), run_status.value)
    await idempotency_repo.complete(
        int(record["id"]),
        status="succeeded" if result.status is ActionStatus.SUCCEEDED else "failed",
        response_status=200,
        response_body=result.model_dump(mode="json"),
        resource_id=result.action_id,
    )
    return result
