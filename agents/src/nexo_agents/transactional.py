"""Agente transaccional (F1.10).

Es el **único** agente que puede escribir, y su superficie es deliberadamente
diminuta: recibe una acción ya confirmada y ejecuta exactamente una tool. No
planifica, no recupera evidencia, no redacta y no decide si la escritura procede
—eso ya se decidió antes de llegar aquí.

Las cinco reglas que lo definen, y por qué ninguna es opcional:

1. **Solo tools marcadas `write`** (`DIE-F1-075`). Ejecutar una lectura desde
   aquí no sería peligroso, pero difuminaría la frontera que hace auditable el
   sistema: si el transaccional puede hacer cualquier cosa, «solo el
   transaccional escribe» deja de significar algo.
2. **Una tool por acción confirmada** (`DIE-F1-076`). Dos escrituras bajo un
   solo consentimiento es consentimiento para una cosa y ejecución de dos.
3. **Sin folio no hay éxito** (`DIE-F1-078`). Un resultado sin identificador
   verificable se reporta `partial`, nunca como éxito inferido.
4. **Outcome desconocido jamás se reintenta** (`DIE-F1-077`). Es el único caso
   en que no sabemos si la operación ocurrió, y reintentar es exactamente cómo
   se duplica una cita.
5. **Se revalida todo en el momento de ejecutar** (`DIE-F1-074`): permiso,
   versión esperada y schema. Entre que la acción se persistió y la persona
   confirmó pueden haber pasado horas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nexo_contracts import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ErrorCode,
    NormalizedError,
    Outcome,
    ToolCall,
    ToolCallStatus,
    ToolMode,
    ToolPermissionContext,
    ToolResult,
    VerifiedFacts,
)

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from nexo_mcp.catalog import ToolCatalog
    from nexo_mcp.execution import ToolExecutor


@dataclass(frozen=True)
class TransactionOutcome:
    """Resultado de ejecutar una acción confirmada."""

    action_result: ActionResult
    tool_result: ToolResult | None = None
    audit: dict[str, str | int | bool] | None = None
    warnings: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.action_result.status is ActionStatus.SUCCEEDED

    @property
    def is_partial(self) -> bool:
        return self.action_result.status is ActionStatus.PARTIAL


@dataclass
class TransactionalAgent:
    """Ejecuta una acción confirmada contra una tool de escritura."""

    catalog: ToolCatalog
    executor: ToolExecutor

    async def execute(
        self,
        action: ActionRequest,
        *,
        facts: VerifiedFacts,
        identity: ToolPermissionContext,
        tool_call_id: str,
        run_id: str,
        trace_id: str,
    ) -> TransactionOutcome:
        """Ejecuta la acción. Nunca lanza: el desenlace viaja en el resultado."""
        from nexo_mcp.execution import audit_payload, has_unknown_outcome

        guard = self._preconditions(action, facts)
        if guard is not None:
            return TransactionOutcome(action_result=guard)

        definition = self.catalog.definition(action.tool_name)
        assert definition is not None  # comprobado en `_preconditions`

        call = ToolCall(
            tool_call_id=tool_call_id,
            name=action.tool_name,
            version=definition.version,
            run_id=run_id,
            trace_id=trace_id,
            context=identity,
            parameters=action.parameters,
            action_id=action.action_id,
            idempotency_key=action.idempotency_key,
            confirmed=action.consent,
            mode=ToolMode.WRITE,
        )

        result = await self.executor.execute(call)
        audit = audit_payload(call, result)

        if result.status is not ToolCallStatus.SUCCEEDED:
            # `DIE-F1-081`: si no podemos verificar el efecto, `partial`. Y no se
            # reintenta: el executor tampoco lo haría, pero decirlo aquí también
            # importa, porque aquí es donde alguien sentiría la tentación.
            unknown = has_unknown_outcome(result)
            return TransactionOutcome(
                action_result=ActionResult(
                    action_id=action.action_id,
                    status=ActionStatus.PARTIAL if unknown else ActionStatus.FAILED,
                    tool_call_id=tool_call_id,
                    error=result.error.error if result.error else None,
                ),
                tool_result=result,
                audit=audit,
                warnings=(
                    (
                        "No pudimos confirmar si la operación se aplicó. No la repetimos "
                        "para no duplicarla: verifícala antes de intentarlo de nuevo.",
                    )
                    if unknown
                    else ()
                ),
            )

        if result.confirmation is None:
            # `DIE-F1-078`: la tool dijo que sí y no trajo folio. No es éxito.
            return TransactionOutcome(
                action_result=ActionResult(
                    action_id=action.action_id,
                    status=ActionStatus.PARTIAL,
                    tool_call_id=tool_call_id,
                    tool_result=result,
                    error=NormalizedError.from_code(
                        ErrorCode.UNKNOWN_OUTCOME,
                        "la operación se reportó exitosa sin identificador verificable",
                        outcome=Outcome.UNKNOWN,
                    ),
                ),
                tool_result=result,
                audit=audit,
                warnings=("La dependencia no devolvió folio; no podemos darla por hecha.",),
            )

        warnings: tuple[str, ...] = ()
        if result.confirmation.is_mock:
            # `DIE-F1-079`: la naturaleza mock se declara de forma visible.
            warnings = (
                f"Folio de demostración {result.confirmation.identifier}: no corresponde "
                f"a un trámite real.",
            )
        if result.idempotency_replayed:
            # `DIE-F1-080`: se propaga el replay sin emitir una segunda escritura.
            warnings = (*warnings, "Esta confirmación ya se había procesado; no se repitió.")

        return TransactionOutcome(
            action_result=ActionResult(
                action_id=action.action_id,
                status=ActionStatus.SUCCEEDED,
                tool_call_id=tool_call_id,
                tool_result=result,
                idempotency_replayed=result.idempotency_replayed,
            ),
            tool_result=result,
            audit=audit,
            warnings=warnings,
        )

    # -- precondiciones (`DIE-F1-073`, `DIE-F1-074`, `DIE-F1-075`) ----------

    def _preconditions(self, action: ActionRequest, facts: VerifiedFacts) -> ActionResult | None:
        """Revalida en el momento de ejecutar. `None` si todo está en orden."""
        if action.status is ActionStatus.PENDING_CONFIRMATION:
            return self._reject(
                action,
                ErrorCode.ACTION_CONFIRMATION_REQUIRED,
                "la acción no ha sido confirmada por la persona usuaria",
            )
        if not action.consent:
            return self._reject(
                action,
                ErrorCode.ACTION_CONFIRMATION_REQUIRED,
                "la acción no transporta consentimiento explícito",
            )
        if action.idempotency_key is None:
            return self._reject(
                action,
                ErrorCode.VALIDATION_ERROR,
                "la acción no transporta idempotency key; reanudar duplicaría el efecto",
            )

        definition = self.catalog.definition(action.tool_name)
        if definition is None:
            return self._reject(
                action, ErrorCode.TOOL_NOT_FOUND, "la tool no está registrada o está deshabilitada"
            )

        # `DIE-F1-075`: solo tools de escritura.
        if definition.metadata.mode is not ToolMode.WRITE:
            return self._reject(
                action,
                ErrorCode.PERMISSION_DENIED,
                f"la tool {action.tool_name!r} no es de escritura; el agente transaccional "
                f"no ejecuta lecturas",
            )

        if action.tool_version != definition.version:
            return self._reject(
                action,
                ErrorCode.VERSION_CONFLICT,
                f"la acción se persistió para la versión {action.tool_version} y la "
                f"registrada es {definition.version}",
            )

        # Una contradicción crítica sin resolver bloquea la escritura aunque
        # todo lo demás esté en orden (§8 de las convenciones).
        if facts.has_blocking_contradiction():
            return self._reject(
                action,
                ErrorCode.PERMISSION_DENIED,
                "hay una contradicción crítica sin resolver que bloquea la escritura",
            )

        # Los hechos que sustentan la acción deben seguir siendo aptos: entre la
        # confirmación y la ejecución, el verificador pudo rechazar uno.
        unsupported = [
            fact_id
            for fact_id in action.supporting_fact_ids
            if (fact := facts.by_id(fact_id)) is None or not fact.write_eligible
        ]
        if unsupported:
            return self._reject(
                action,
                ErrorCode.PERMISSION_DENIED,
                f"la acción se apoya en hechos que ya no sustentan una escritura: "
                f"{sorted(unsupported)}",
            )
        return None

    @staticmethod
    def _reject(action: ActionRequest, code: ErrorCode, message: str) -> ActionResult:
        return ActionResult(
            action_id=action.action_id,
            status=ActionStatus.FAILED,
            error=NormalizedError.from_code(code, message, outcome=Outcome.KNOWN_FAILURE),
        )
