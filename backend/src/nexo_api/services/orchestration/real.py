"""Orquestador real: corre el grafo MVP y persiste la acción pendiente.

Implementa el puerto `Orchestrator` sobre el `MVPGraph` ensamblado. Como la
confirmación HTTP no reanuda el grafo (ejecuta un `ActionExecutor` bajo el ledger
de idempotencia), el grafo solo corre hasta `waiting_confirmation`; aquí se
extrae la `ActionRequest` del checkpoint y se persiste para que el cliente pueda
confirmarla.
"""

from __future__ import annotations

from nexo_api.services.orchestration.assembly import GraphAssembly
from nexo_api.services.orchestration.port import PendingActionSink
from nexo_contracts import RunRequest, RunResult, RunStatus
from nexo_orchestration.graph.mvp import MVPGraph
from nexo_orchestration.ports import EventSinkPort
from nexo_orchestration.testing import InMemoryCheckpointStore


class RealOrchestrator:
    def __init__(self, assembly: GraphAssembly) -> None:
        self._assembly = assembly

    async def run(
        self,
        request: RunRequest,
        event_sink: EventSinkPort,
        pending_actions: PendingActionSink,
        *,
        tenant_id: int,
    ) -> RunResult:
        # El checkpoint vive por-run: no se reanuda vía grafo, solo se usa para
        # recuperar el estado final (y su acción pendiente) tras `invoke`.
        checkpoints = InMemoryCheckpointStore()
        graph = MVPGraph(
            deps=self._assembly.deps,
            event_sink=event_sink,
            checkpoints=checkpoints,
            clock=self._assembly.clock,
            ids=self._assembly.ids,
            policies=self._assembly.policies,
            valid_at=self._assembly.valid_at,
        )
        # El backend construye RunRequest sin exponer presupuestos al cliente.
        # Aplicar aquí el perfil cargado evita que el default del contrato (20 s)
        # contradiga, por ejemplo, el presupuesto mayor que Gemini necesita al
        # sumar inferencia y persistencia remota de la traza.
        effective_request = request.model_copy(
            update={"budgets": self._assembly.policies.run_budgets}
        )
        result = await graph.invoke(effective_request)

        if result.status is RunStatus.WAITING_CONFIRMATION:
            state = await checkpoints.load(request.run_id)
            if state is not None and state.pending_action is not None:
                await pending_actions.persist(state.pending_action, tenant_id=tenant_id)

        return result
