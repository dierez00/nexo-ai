"""Grafo mínimo de Fase 0: `start → classify_fake → finalize_fake` (`DIE-F0-038`).

Su objetivo no es clasificar bien, sino demostrar que la mecánica completa
funciona sin proveedor, base de datos ni credenciales: un `RunRequest` entra, el
grafo emite eventos válidos y secuenciados, guarda checkpoints, respeta el
deadline y produce un `RunResult` determinista.

`classify_fake` y `finalize_fake` son andamiaje explícito de Fase 0. El
clasificador real, con su prompt versionado y su fallback determinista, es
trabajo de Fase 1 (F1.4); los nodos completos del MVP están en F1.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import Field, ValidationError

from nexo_contracts import (
    ActorType,
    Confidence,
    Domain,
    ErrorCode,
    EventStatus,
    EventType,
    ModelTaskKind,
    NexoModel,
    NormalizedError,
    RunRequest,
    RunResult,
    RunState,
    RunStatus,
)
from nexo_contracts.config import PoliciesConfig

from ..events import EventEmitter
from ..ports.checkpoints import CheckpointStorePort
from ..ports.clock import Clock, IdFactory
from ..ports.events import EventSinkPort
from ..ports.model import ChatModelPort, ChatRequest, ModelPortError
from ..reducers import merge_run_state

NODE_START = "start"
NODE_CLASSIFY = "classify_fake"
NODE_FINALIZE = "finalize_fake"

CLASSIFY_PURPOSE = "classify_request"


class FakeClassification(NexoModel):
    """Salida esperada del modelo en `classify_fake`.

    Andamiaje de Fase 0: valida que el gateway devuelve algo con forma conocida
    y que una salida inválida se detecta. El contrato real del clasificador
    (dominios múltiples, intenciones, entidades, faltantes) se define en F1.4.
    """

    domain: Domain
    confidence: Confidence = Field(default=0.5)


class GraphState(TypedDict):
    """Estado que LangGraph transporta entre nodos.

    Envuelve `RunState` en lugar de anotarlo directamente: así el contrato
    publicado no necesita conocer los reducers ni el framework del grafo (§4.1).
    """

    run: Annotated[RunState, merge_run_state]


class RunDeadlineExceededError(Exception):
    """El run agotó su deadline antes de completar un nodo."""


@dataclass
class MinimalGraph:
    """Grafo mínimo con todos sus puertos inyectados.

    Ninguna dependencia es concreta: sustituir el modelo falso por un adapter,
    o el almacén en memoria por PostgreSQL, no cambia este código
    (`DIE-F0-030`).
    """

    model: ChatModelPort
    event_sink: EventSinkPort
    checkpoints: CheckpointStorePort
    clock: Clock
    ids: IdFactory
    policies: PoliciesConfig

    def __post_init__(self) -> None:
        self.emitter = EventEmitter(
            sink=self.event_sink,
            clock=self.clock,
            ids=self.ids,
            policy_version=self.policies.version,
        )
        self._compiled = self._build()

    # -- construcción ----------------------------------------------------

    def _build(self) -> Any:
        graph = StateGraph(GraphState)
        graph.add_node(NODE_START, self._start)
        graph.add_node(NODE_CLASSIFY, self._classify_fake)
        graph.add_node(NODE_FINALIZE, self._finalize_fake)
        graph.add_edge(START, NODE_START)
        graph.add_edge(NODE_START, NODE_CLASSIFY)
        graph.add_edge(NODE_CLASSIFY, NODE_FINALIZE)
        graph.add_edge(NODE_FINALIZE, END)
        return graph.compile()

    # -- utilidades de nodo ----------------------------------------------

    def _elapsed_ms(self, state: RunState) -> int:
        """Milisegundos transcurridos desde que se recibió la solicitud.

        Se calcula contra `received_at`, que viaja en el estado, para que la
        cuenta sobreviva a una reanudación desde checkpoint.
        """
        delta = self.clock.now() - state.request.received_at
        return max(0, int(delta.total_seconds() * 1000))

    def _check_deadline(self, state: RunState) -> None:
        """Aplica el deadline del run (`DIE-F0-043`)."""
        if self._elapsed_ms(state) > state.request.budgets.deadline_ms:
            raise RunDeadlineExceededError(
                f"el run superó su deadline de {state.request.budgets.deadline_ms} ms"
            )

    def _outcome_status(self, code: ErrorCode) -> RunStatus:
        """Traduce un error a estado terminal según la política (`DIE-F0-010`)."""
        if self.policies.outcomes.is_partial(code):
            return RunStatus.PARTIAL
        return RunStatus.FAILED

    async def _persist(self, state: RunState, node: str) -> RunState:
        """Confirma el nodo, emite `checkpoint.saved` y persiste (`DIE-F0-041`).

        El orden importa: primero se emite el evento y después se guarda el
        estado, de modo que el `event_cursor` persistido incluya ese evento. Al
        revés, el checkpoint quedaría una posición atrás y la reanudación
        intentaría reutilizar una secuencia ya emitida.
        """
        confirmed = state.model_copy(
            update={
                "completed_nodes": sorted({*state.completed_nodes, node}),
                "updated_at": self.clock.now(),
            }
        )
        checkpoint_id = self.ids.new_id("chk")
        confirmed = await self.emitter.checkpoint_saved(confirmed, node, checkpoint_id)
        await self.checkpoints.save(confirmed, node=node, checkpoint_id=checkpoint_id)
        return confirmed

    async def _fail(self, state: RunState, node: str, error: NormalizedError) -> GraphState:
        failed = await self.emitter.node_failed(state, node, error, duration_ms=0)
        failed = failed.model_copy(
            update={"status": self._outcome_status(error.code), "error": error}
        )
        failed = await self.emitter.emit(
            failed,
            EventType.RUN_PARTIAL if failed.status is RunStatus.PARTIAL else EventType.RUN_FAILED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.FAILED,
            error=error,
        )
        return {"run": await self._persist(failed, node)}

    # -- nodos ------------------------------------------------------------

    async def _start(self, state: GraphState) -> GraphState:
        run = state["run"]
        if run.has_completed(NODE_START):
            return {"run": await self.emitter.node_skipped(run, NODE_START)}

        started = await self.emitter.node_started(run, NODE_START)
        started = started.model_copy(update={"status": RunStatus.RUNNING})
        started = await self.emitter.emit(
            started,
            EventType.RUN_STARTED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        started = await self.emitter.node_completed(started, NODE_START, duration_ms=0)
        return {"run": await self._persist(started, NODE_START)}

    async def _classify_fake(self, state: GraphState) -> GraphState:
        run = state["run"]
        if run.has_completed(NODE_CLASSIFY):
            return {"run": await self.emitter.node_skipped(run, NODE_CLASSIFY)}

        current = await self.emitter.node_started(run, NODE_CLASSIFY)
        current = await self.emitter.emit(
            current,
            EventType.CLASSIFICATION_STARTED,
            actor_type=ActorType.AGENT,
            actor_name="classifier_fake",
            status=EventStatus.STARTED,
        )

        try:
            self._check_deadline(current)
        except RunDeadlineExceededError as exc:
            return await self._fail(
                current,
                NODE_CLASSIFY,
                NormalizedError.from_code(ErrorCode.RUN_TIMEOUT, str(exc)),
            )

        started_ms = self.clock.monotonic_ms()
        try:
            response = await self.model.generate(
                ChatRequest(
                    purpose=CLASSIFY_PURPOSE,
                    task_kind=ModelTaskKind.CLASSIFICATION,
                    alias=self.policies_alias(),
                    output_contract="fake_classification",
                    prompt=current.request.user_message,
                    variables={"channel": current.request.channel.value},
                    deadline_ms=3000,
                )
            )
        except ModelPortError as exc:
            return await self._fail(current, NODE_CLASSIFY, exc.error)

        try:
            classification = FakeClassification.model_validate(response.data)
        except ValidationError as exc:
            # Salida inválida: es un fallo del modelo, no del contrato del run.
            error = NormalizedError.from_code(
                ErrorCode.MODEL_OUTPUT_INVALID,
                f"la salida del modelo no cumple 'fake_classification': {exc.errors()[0]['msg']}",
            )
            return await self._fail(current, NODE_CLASSIFY, error)

        duration = self.clock.monotonic_ms() - started_ms
        current = current.model_copy(
            update={
                "domain": classification.domain,
                "metrics": current.metrics.model_copy(
                    update={
                        "model_invocation_count": current.metrics.model_invocation_count + 1,
                        "total_input_tokens": (
                            current.metrics.total_input_tokens + response.input_tokens
                        ),
                        "total_output_tokens": (
                            current.metrics.total_output_tokens + response.output_tokens
                        ),
                        "total_cost_usd": (
                            current.metrics.total_cost_usd + response.estimated_cost_usd
                        ),
                    }
                ),
            }
        )
        current = await self.emitter.emit(
            current,
            EventType.CLASSIFICATION_COMPLETED,
            actor_type=ActorType.AGENT,
            actor_name="classifier_fake",
            status=EventStatus.SUCCEEDED,
            duration_ms=duration,
            data={"domain": classification.domain.value, "confidence": classification.confidence},
        )
        current = await self.emitter.node_completed(current, NODE_CLASSIFY, duration_ms=duration)
        return {"run": await self._persist(current, NODE_CLASSIFY)}

    async def _finalize_fake(self, state: GraphState) -> GraphState:
        run = state["run"]
        if run.has_completed(NODE_FINALIZE):
            return {"run": await self.emitter.node_skipped(run, NODE_FINALIZE)}
        if run.status in {RunStatus.FAILED, RunStatus.PARTIAL}:
            # Un run que ya falló no se "finaliza con éxito" por llegar al final
            # del grafo.
            return {"run": run}

        current = await self.emitter.node_started(run, NODE_FINALIZE)
        current = current.model_copy(
            update={
                "status": RunStatus.SUCCEEDED,
                "answer": (
                    "Solicitud clasificada en el dominio "
                    f"'{current.domain.value if current.domain else 'desconocido'}'. "
                    "Respuesta de andamiaje de Fase 0."
                ),
                "metrics": current.metrics.model_copy(
                    update={"duration_ms": self._elapsed_ms(current)}
                ),
            }
        )
        current = await self.emitter.node_completed(current, NODE_FINALIZE, duration_ms=0)
        current = await self.emitter.emit(
            current,
            EventType.RUN_COMPLETED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        return {"run": await self._persist(current, NODE_FINALIZE)}

    # -- API pública -------------------------------------------------------

    def policies_alias(self) -> str:
        """Alias con el que se invoca al modelo en el perfil offline."""
        return "offline_fake"

    def initial_state(self, request: RunRequest) -> RunState:
        now = self.clock.now()
        return RunState(
            run_id=request.run_id,
            trace_id=request.trace_id,
            conversation_id=request.conversation_id,
            status=RunStatus.QUEUED,
            request=request,
            created_at=now,
            updated_at=now,
            policy_version=self.policies.version,
        )

    async def invoke(self, request: RunRequest) -> RunResult:
        """Ejecuta el grafo completo y devuelve el resultado proyectado."""
        state = self.initial_state(request)
        state = await self.emitter.emit(
            state,
            EventType.RUN_QUEUED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        final: GraphState = await self._compiled.ainvoke({"run": state})
        return RunResult.from_state(final["run"])

    async def resume(self, run_id: str) -> RunResult:
        """Reanuda desde el último checkpoint sin repetir nodos confirmados.

        Los nodos ya completados se registran como `skipped` en la traza en vez
        de volver a ejecutarse (`DIE-F0-042`).
        """
        state = await self.checkpoints.load(run_id)
        if state is None:
            raise LookupError(f"no hay checkpoint para el run {run_id!r}")
        state = await self.emitter.emit(
            state,
            EventType.CHECKPOINT_RESTORED,
            actor_type=ActorType.SYSTEM,
            actor_name="checkpoint_store",
            status=EventStatus.SUCCEEDED,
            data={"completed_nodes": list(state.completed_nodes)},
        )
        final: GraphState = await self._compiled.ainvoke({"run": state})
        return RunResult.from_state(final["run"])
