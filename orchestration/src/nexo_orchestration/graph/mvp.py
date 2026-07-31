"""Grafo MVP secuencial con confirmación y reanudación (F1.11).

Doce nodos (`DIE-F1-083`), en orden:

    normalize → classify → plan → retrieve → navigate → read_tools →
    verify → estimate → merge → build_a2ui → write_answer → finalize

**Verificador y estimador son secuenciales en el MVP** (`DIE-F1-084`). Los
contratos ya admiten el fan-out de Fase 4 —las skills declaran qué pasos son
paralelizables y los reducers consolidan sin depender del orden— pero
ejecutarlos en paralelo ahora añadiría una fuente de no determinismo antes de
tener un baseline con el que comparar.

**El interrupt es el corazón del recorrido** (`DIE-F1-085`…`087`). Cuando hay una
escritura pendiente, el run **termina** en `waiting_confirmation` con la acción
persistida en el checkpoint, con su schema y su versión esperada. Reanudar carga
ese checkpoint, marca la acción confirmada y vuelve a invocar el grafo: los
nodos ya completados se registran como `skipped` en la traza en vez de
reejecutarse (`DIE-F1-088`), así que no se vuelve a recuperar evidencia, ni a
invocar tools de lectura, ni a redactar.

Esa mecánica es la misma del grafo mínimo de Fase 0, que se construyó
precisamente para esto: `completed_nodes` viaja en el estado, el estado se
persiste, y el `event_cursor` mantiene la secuencia sin huecos entre la
ejecución original y la reanudación.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, TypedDict, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import JsonValue

from nexo_contracts import (
    TERMINAL_RUN_STATUSES,
    ActionRequest,
    ActionStatus,
    ActorType,
    CandidateFact,
    Channel,
    ChannelFallback,
    Domain,
    ErrorCode,
    Estimate,
    EventStatus,
    EventType,
    EventVisibility,
    ModelInvocation,
    NormalizedError,
    Outcome,
    RunRequest,
    RunResult,
    RunState,
    RunStatus,
    ToolCall,
    ToolMode,
    ToolPermissionContext,
    ToolResult,
)
from nexo_contracts.config import PoliciesConfig
from nexo_contracts.primitives import UtcDatetime

from ..events import EventEmitter
from ..models import BudgetLedger, ModelCallContext, ModelGateway
from ..ports.checkpoints import CheckpointStorePort
from ..ports.clock import Clock, IdFactory
from ..ports.events import EventSinkPort

if TYPE_CHECKING:
    from nexo_a2ui import CitizenSurfaceBuilder, SurfaceValidator
    from nexo_agents.catalog import CentralCatalog
    from nexo_agents.classifier import Classifier
    from nexo_agents.estimator import Estimator
    from nexo_agents.navigator import DomainNavigator
    from nexo_agents.transactional import TransactionalAgent
    from nexo_agents.verifier import Verifier
    from nexo_agents.writer import Writer
    from nexo_mcp.catalog import ToolCatalog
    from nexo_mcp.execution import ToolExecutor

NODE_NORMALIZE = "normalize"
NODE_CLASSIFY = "classify"
NODE_PLAN = "plan"
NODE_NAVIGATE = "navigate"
NODE_RETRIEVE = "retrieve"
NODE_READ_TOOLS = "read_tools"
NODE_VERIFY = "verify"
NODE_ESTIMATE = "estimate"
NODE_MERGE = "merge"
NODE_BUILD_A2UI = "build_a2ui"
NODE_WRITE_ANSWER = "write_answer"
NODE_FINALIZE = "finalize"

_TERMINAL_EVENT: dict[RunStatus, EventType] = {
    RunStatus.SUCCEEDED: EventType.RUN_COMPLETED,
    RunStatus.PARTIAL: EventType.RUN_PARTIAL,
    RunStatus.WAITING_CONFIRMATION: EventType.RUN_WAITING_CONFIRMATION,
    RunStatus.FAILED: EventType.RUN_FAILED,
}

NODES = (
    NODE_NORMALIZE,
    NODE_CLASSIFY,
    NODE_PLAN,
    NODE_NAVIGATE,
    NODE_RETRIEVE,
    NODE_READ_TOOLS,
    NODE_VERIFY,
    NODE_ESTIMATE,
    NODE_MERGE,
    NODE_BUILD_A2UI,
    NODE_WRITE_ANSWER,
    NODE_FINALIZE,
)


class GraphState(TypedDict):
    """Estado de LangGraph; todo lo reanudable vive dentro de `RunState`."""

    run: RunState


@dataclass
class MVPDependencies:
    """Todo lo que el grafo necesita, inyectado.

    Se agrupa en un objeto y no en doce parámetros porque la lista completa es
    lo que define el alcance del MVP, y verla junta hace evidente qué falta y
    qué sobra.
    """

    gateway: ModelGateway
    classifier: Classifier
    navigators: dict[Domain, DomainNavigator]
    verifier_factory: Callable[[UtcDatetime, date], Verifier]
    estimators: dict[Domain, Estimator]
    writer: Writer
    transactional: TransactionalAgent
    catalog: ToolCatalog
    executor: ToolExecutor
    tool_fact_projector: Callable[
        [Sequence[ToolResult], Domain],
        Sequence[CandidateFact],
    ]
    surface_builder: CitizenSurfaceBuilder | None = None
    surface_validator: SurfaceValidator | None = None
    central_catalog: CentralCatalog | None = None


@dataclass
class MVPGraph:
    """Grafo secuencial del MVP con interrupt antes de cada escritura."""

    deps: MVPDependencies
    event_sink: EventSinkPort
    checkpoints: CheckpointStorePort
    clock: Clock
    ids: IdFactory
    policies: PoliciesConfig
    valid_at: date = field(default_factory=lambda: date(2026, 7, 30))

    def __post_init__(self) -> None:
        self.emitter = EventEmitter(
            sink=self.event_sink,
            clock=self.clock,
            ids=self.ids,
            policy_version=self.policies.version,
        )
        self._compiled = self._build()

    def _build(self) -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:
        graph: StateGraph[GraphState, None, GraphState, GraphState] = StateGraph(GraphState)
        handlers = {
            NODE_NORMALIZE: self._normalize,
            NODE_CLASSIFY: self._classify,
            NODE_PLAN: self._plan,
            NODE_RETRIEVE: self._retrieve,
            NODE_NAVIGATE: self._navigate,
            NODE_READ_TOOLS: self._read_tools,
            NODE_VERIFY: self._verify,
            NODE_ESTIMATE: self._estimate,
            NODE_MERGE: self._merge,
            NODE_BUILD_A2UI: self._build_a2ui,
            NODE_WRITE_ANSWER: self._write_answer,
            NODE_FINALIZE: self._finalize,
        }
        for name, handler in handlers.items():
            graph.add_node(name, handler)

        # Orden ratificado: navegar requiere evidencia recuperada.
        order = [
            NODE_NORMALIZE,
            NODE_CLASSIFY,
            NODE_PLAN,
            NODE_RETRIEVE,
            NODE_NAVIGATE,
            NODE_READ_TOOLS,
            NODE_VERIFY,
            NODE_ESTIMATE,
            NODE_MERGE,
            NODE_BUILD_A2UI,
            NODE_WRITE_ANSWER,
            NODE_FINALIZE,
        ]
        graph.add_edge(START, order[0])
        for current, following in zip(order, order[1:], strict=False):
            graph.add_edge(current, following)
        graph.add_edge(order[-1], END)
        return graph.compile()

    # -- utilidades ---------------------------------------------------------

    def _elapsed_ms(self, state: RunState) -> int:
        delta = self.clock.now() - state.request.received_at
        return max(0, int(delta.total_seconds() * 1000))

    def _ledger(self, state: RunState) -> BudgetLedger:
        """Presupuesto del run con el tiempo ya consumido (`DIE-F1-089`)."""
        ledger = BudgetLedger(
            budgets=state.request.budgets,
            spent_usd=state.metrics.total_cost_usd,
            spent_tokens=state.metrics.total_input_tokens + state.metrics.total_output_tokens,
        )
        ledger.observe_elapsed(self._elapsed_ms(state))
        return ledger

    def _context(self, state: RunState) -> ModelCallContext:
        return ModelCallContext(
            run_id=state.run_id, trace_id=state.trace_id, ledger=self._ledger(state)
        )

    def _charge(
        self,
        state: RunState,
        invocations: Sequence[ModelInvocation],
        ledger: BudgetLedger,
    ) -> RunState:
        """Acumula el consumo de un nodo en las métricas del run."""
        metrics = state.metrics.model_copy(
            update={
                "model_invocation_count": state.metrics.model_invocation_count + len(invocations),
                "total_cost_usd": ledger.spent_usd,
                "total_input_tokens": sum(i.input_tokens for i in invocations)
                + state.metrics.total_input_tokens,
                "total_output_tokens": sum(i.output_tokens for i in invocations)
                + state.metrics.total_output_tokens,
            }
        )
        return state.model_copy(
            update={
                "metrics": metrics,
                "model_invocations": [*state.model_invocations, *invocations],
            }
        )

    async def _emit_model_events(
        self, state: RunState, invocations: Sequence[ModelInvocation]
    ) -> RunState:
        """Proyecta invocaciones ya minimizadas para replay del workflow."""
        current = state
        for invocation in invocations:
            decision = invocation.decision
            if invocation.attempt > 1:
                current = await self.emitter.emit(
                    current,
                    EventType.AGENT_RETRIED,
                    actor_type=ActorType.MODEL,
                    actor_name=decision.selected_alias,
                    status=EventStatus.STARTED,
                    data={"attempt": invocation.attempt},
                    public_data={"attempt": invocation.attempt},
                )
            if decision.selected_alias != decision.requested_alias:
                current = await self.emitter.emit(
                    current,
                    EventType.MODEL_FALLBACK,
                    actor_type=ActorType.MODEL,
                    actor_name=decision.selected_alias,
                    status=EventStatus.SUCCEEDED,
                    data={
                        "requested_alias": decision.requested_alias,
                        "selected_alias": decision.selected_alias,
                        "reason": decision.reason.value,
                    },
                    public_data={"reason": decision.reason.value},
                    visibility=EventVisibility.RESTRICTED,
                )
            current = await self.emitter.emit(
                current,
                EventType.MODEL_SELECTED,
                actor_type=ActorType.MODEL,
                actor_name=decision.selected_alias,
                status=EventStatus.SUCCEEDED,
                data={
                    "invocation_id": invocation.invocation_id,
                    "selected_alias": decision.selected_alias,
                    "attempt": invocation.attempt,
                },
                public_data={"attempt": invocation.attempt},
                visibility=EventVisibility.RESTRICTED,
            )
            failed = invocation.error is not None
            current = await self.emitter.emit(
                current,
                EventType.MODEL_FAILED if failed else EventType.MODEL_COMPLETED,
                actor_type=ActorType.MODEL,
                actor_name=decision.selected_alias,
                status=EventStatus.FAILED if failed else EventStatus.SUCCEEDED,
                duration_ms=invocation.duration_ms,
                data={
                    "invocation_id": invocation.invocation_id,
                    "input_units": invocation.input_tokens,
                    "output_units": invocation.output_tokens,
                    "schema_valid": invocation.schema_valid,
                },
                public_data={
                    "schema_valid": invocation.schema_valid,
                },
                visibility=EventVisibility.RESTRICTED,
                error=invocation.error,
            )
        return current

    async def _skip_or_start(self, state: GraphState, node: str) -> RunState | None:
        """`None` si el nodo debe ejecutarse; el estado ya avanzado si se salta.

        Un nodo se salta por dos motivos distintos: ya estaba confirmado en un
        checkpoint anterior (`DIE-F1-088`), o el run ya terminó y llegar aquí es
        solo el grafo desenrollándose.

        `waiting_confirmation` **no** salta nada. Interrumpir significa «no
        ejecutes la escritura», no «no respondas»: la persona debe ver los
        requisitos, los costos, las fuentes y el botón antes de decidir. Saltar
        aquí dejaba el run esperando confirmación de algo que nunca se le
        mostró.
        """
        run = state["run"]
        if run.has_completed(node):
            # Saltar **también persiste**. El evento de salto avanza el
            # `event_cursor`, y si no se guardara, el checkpoint quedaría una
            # posición atrás de la traza: la siguiente reanudación intentaría
            # reutilizar una secuencia ya emitida y el sink la rechazaría.
            #
            # Es la misma clase de error que H-01 de Fase 0, reaparecida en otra
            # forma. La regla general que lo evita: todo nodo que emite un
            # evento deja el checkpoint consistente antes de devolver.
            return await self._persist(await self.emitter.node_skipped(run, node), node)
        if run.status in TERMINAL_RUN_STATUSES:
            return run
        return None

    async def _persist(self, state: RunState, node: str) -> RunState:
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
        status = (
            RunStatus.PARTIAL if self.policies.outcomes.is_partial(error.code) else RunStatus.FAILED
        )
        failed = failed.model_copy(update={"status": status, "error": error})
        failed = await self.emitter.emit(
            failed,
            EventType.RUN_PARTIAL if status is RunStatus.PARTIAL else EventType.RUN_FAILED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.FAILED,
            error=error,
        )
        return _graph(await self._persist(failed, node))

    def _check_budget(self, state: RunState) -> NormalizedError | None:
        """`DIE-F1-089`: el deadline se comprueba en el supervisor, nodo a nodo."""
        if self._elapsed_ms(state) > state.request.budgets.deadline_ms:
            return NormalizedError.from_code(
                ErrorCode.RUN_TIMEOUT,
                f"el run superó su deadline de {state.request.budgets.deadline_ms} ms",
                outcome=Outcome.KNOWN_FAILURE,
            )
        if state.metrics.total_cost_usd > state.request.budgets.max_cost_usd:
            return NormalizedError.from_code(
                ErrorCode.BUDGET_EXCEEDED, "el run agotó su presupuesto de costo"
            )
        return None

    # -- nodos --------------------------------------------------------------

    async def _normalize(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_NORMALIZE)
        if skipped is not None:
            return _graph(skipped)

        run = await self.emitter.node_started(state["run"], NODE_NORMALIZE)
        run = run.model_copy(update={"status": RunStatus.RUNNING})
        run = await self.emitter.emit(
            run,
            EventType.RUN_STARTED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        run = await self.emitter.node_completed(run, NODE_NORMALIZE, duration_ms=0)
        return _graph(await self._persist(run, NODE_NORMALIZE))

    async def _classify(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_CLASSIFY)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        if (error := self._check_budget(run)) is not None:
            return await self._fail(run, NODE_CLASSIFY, error)

        run = await self.emitter.node_started(run, NODE_CLASSIFY)
        run = await self.emitter.emit(
            run,
            EventType.CLASSIFICATION_STARTED,
            actor_type=ActorType.AGENT,
            actor_name="classifier",
            status=EventStatus.STARTED,
        )

        ledger = self._ledger(run)
        context = ModelCallContext(run_id=run.run_id, trace_id=run.trace_id, ledger=ledger)
        outcome = await self.deps.classifier.classify(run.request, context)

        run = self._charge(run, outcome.invocations, ledger)
        run = await self._emit_model_events(run, outcome.invocations)
        classification = outcome.classification
        run = run.model_copy(
            update={
                "domain": classification.primary_domain,
                "classification": classification,
                "status": RunStatus.PLANNING,
                "warnings": (
                    [*run.warnings, "La clasificación usó el respaldo determinista."]
                    if outcome.used_fallback
                    else run.warnings
                ),
            }
        )
        run = await self.emitter.emit(
            run,
            EventType.CLASSIFICATION_COMPLETED,
            actor_type=ActorType.AGENT,
            actor_name="classifier",
            status=EventStatus.SUCCEEDED,
            data={
                "intents": list(classification.intent_slugs()),
                "domain": classification.primary_domain.value
                if classification.primary_domain
                else "",
                "used_fallback": outcome.used_fallback,
            },
        )
        run = await self.emitter.node_completed(run, NODE_CLASSIFY, duration_ms=0)
        return _graph(await self._persist(run, NODE_CLASSIFY))

    async def _plan(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_PLAN)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        domain = run.domain
        if domain is None:
            # Sin dominio no hay a quién delegar. No es un fallo del sistema:
            # es una solicitud fuera de alcance, y se responde como tal.
            run = run.model_copy(
                update={
                    "warnings": [
                        *run.warnings,
                        "La solicitud no corresponde a los trámites que puedo atender.",
                    ]
                }
            )
            run = await self.emitter.node_completed(run, NODE_PLAN, duration_ms=0)
            return _graph(await self._persist(run, NODE_PLAN))

        run = await self.emitter.node_started(run, NODE_PLAN)
        central = self.deps.central_catalog
        if central is not None:
            manifest = central.domain(domain)
            if manifest is None:
                return await self._fail(
                    run,
                    NODE_PLAN,
                    NormalizedError.from_code(
                        ErrorCode.CONFIGURATION_INVALID,
                        f"el dominio {domain.value!r} no está activo en el catálogo central",
                    ),
                )
            visible = await central.visible_tools(
                institution_id=run.request.identity.institution_id,
                roles=list(run.request.identity.roles),
                domain=domain,
            )
            intents = run.classification.intent_slugs() if run.classification else ()
            selected = central.select_skill(domain, intents)
            run = run.model_copy(
                update={
                    "catalog_version": central.snapshot.version,
                    "active_skill_id": selected[0] if selected else None,
                    "active_skill_version": selected[1] if selected else None,
                }
            )
        else:
            visible = frozenset()
        run = run.model_copy(update={"status": RunStatus.RUNNING})
        run = await self.emitter.emit(
            run,
            EventType.PLAN_CREATED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
            data={
                "domain": domain.value,
                "catalog_version": run.catalog_version,
                "visible_tools": len(visible),
                "skill_id": run.active_skill_id or "",
            },
        )
        run = await self.emitter.node_completed(run, NODE_PLAN, duration_ms=0)
        return _graph(await self._persist(run, NODE_PLAN))

    async def _retrieve(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_RETRIEVE)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        navigator = self._navigator(run)
        if navigator is None:
            run = await self.emitter.node_completed(run, NODE_RETRIEVE, duration_ms=0)
            return _graph(await self._persist(run, NODE_RETRIEVE))

        run = await self.emitter.node_started(run, NODE_RETRIEVE)
        run = await self.emitter.emit(
            run,
            EventType.RAG_STARTED,
            actor_type=ActorType.RETRIEVER,
            actor_name="hybrid_retriever",
            status=EventStatus.STARTED,
        )

        classification = run.classification
        intents = (
            [intent for intent in classification.intents if intent.domain is run.domain]
            if classification is not None
            else []
        )
        query = navigator.query_for(run.request, intents)
        results = await navigator.retrieve(query, run.request, self.valid_at)

        run = run.model_copy(
            update={
                "metrics": run.metrics.model_copy(
                    update={"retrieval_count": run.metrics.retrieval_count + 1}
                )
            }
        )
        run = await self.emitter.emit(
            run,
            EventType.RAG_COMPLETED,
            actor_type=ActorType.RETRIEVER,
            actor_name="hybrid_retriever",
            status=EventStatus.SUCCEEDED,
            data={
                "results": len(results),
                "flagged": sum(1 for r in results if r.injection_signals),
            },
        )
        run = await self.emitter.node_completed(run, NODE_RETRIEVE, duration_ms=0)
        run = run.model_copy(update={"retrieval_results": results})
        return _graph(await self._persist(run, NODE_RETRIEVE))

    async def _navigate(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_NAVIGATE)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        navigator = self._navigator(run)
        if navigator is None:
            run = await self.emitter.node_completed(run, NODE_NAVIGATE, duration_ms=0)
            return _graph(await self._persist(run, NODE_NAVIGATE))

        if (error := self._check_budget(run)) is not None:
            return await self._fail(run, NODE_NAVIGATE, error)

        run = await self.emitter.node_started(run, NODE_NAVIGATE)
        ledger = self._ledger(run)
        context = ModelCallContext(run_id=run.run_id, trace_id=run.trace_id, ledger=ledger)

        classification = run.classification
        if classification is None:
            return await self._fail(
                run,
                NODE_NAVIGATE,
                NormalizedError.from_code(
                    ErrorCode.CONTRACT_INVALID,
                    "el run no conserva la clasificación necesaria para navegar",
                ),
            )

        result = await navigator.navigate(
            run.request,
            classification,
            context,
            valid_at=self.valid_at,
            evidence=run.retrieval_results,
        )

        run = self._charge(run, result.invocations, ledger)
        run = await self._emit_model_events(run, result.invocations)
        questions = list(run.questions)
        if result.question is not None and result.question not in questions:
            questions.append(result.question)
        run = run.model_copy(
            update={
                "candidate_facts": [*run.candidate_facts, *result.facts],
                "proposed_tools": list(result.proposed_tools),
                "warnings": [*run.warnings, *result.warnings],
                "questions": questions,
                "metrics": run.metrics.model_copy(update={"question_count": len(questions)}),
            }
        )
        run = await self.emitter.node_completed(run, NODE_NAVIGATE, duration_ms=0)
        return _graph(await self._persist(run, NODE_NAVIGATE))

    async def _read_tools(self, state: GraphState) -> GraphState:
        """Ejecuta las tools de **lectura** propuestas por el navegador.

        Nunca una escritura: el navegador no puede proponerlas, el executor las
        revalida y el agente transaccional es el único que puede pedirlas.
        """
        skipped = await self._skip_or_start(state, NODE_READ_TOOLS)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        proposed = run.proposed_tools
        normalized_proposals = []
        results: list[ToolResult] = []

        if proposed:
            run = await self.emitter.node_started(run, NODE_READ_TOOLS)
        for index, tool in enumerate(proposed):
            definition = self.deps.catalog.definition(tool.name)
            if definition is None or definition.metadata.mode is ToolMode.WRITE:
                continue
            effective = tool.model_copy(update={"mode": definition.metadata.mode})
            normalized_proposals.append(effective)
            run = await self.emitter.emit(
                run,
                EventType.TOOL_REQUESTED,
                actor_type=ActorType.AGENT,
                actor_name="domain_navigator",
                status=EventStatus.STARTED,
                data={"tool": tool.name, "mode": effective.mode.value},
            )
            call = ToolCall(
                tool_call_id=self.ids.new_id("tc"),
                name=effective.name,
                version=definition.version,
                run_id=run.run_id,
                trace_id=run.trace_id,
                context=_permission_context(run),
                parameters=effective.parameters,
                mode=definition.metadata.mode,
            )
            result = await self.deps.executor.execute(call)
            results.append(result)
            run = await self.emitter.emit(
                run,
                EventType.TOOL_COMPLETED
                if result.status.value == "succeeded"
                else EventType.TOOL_FAILED,
                actor_type=ActorType.TOOL,
                actor_name=effective.name,
                status=EventStatus.SUCCEEDED
                if result.status.value == "succeeded"
                else EventStatus.FAILED,
                data={"tool": effective.name, "index": index},
                error=result.error.error if result.error else None,
            )

        run = run.model_copy(
            update={
                "metrics": run.metrics.model_copy(
                    update={"tool_call_count": run.metrics.tool_call_count + len(results)}
                )
            }
        )
        if proposed:
            run = await self.emitter.node_completed(run, NODE_READ_TOOLS, duration_ms=0)
        tool_facts = (
            list(self.deps.tool_fact_projector(results, run.domain))
            if run.domain is not None
            else []
        )
        run = run.model_copy(
            update={
                "candidate_facts": [*run.candidate_facts, *tool_facts],
                "proposed_tools": normalized_proposals,
                "tool_results": results,
            }
        )
        return _graph(await self._persist(run, NODE_READ_TOOLS))

    async def _verify(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_VERIFY)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        run = await self.emitter.node_started(run, NODE_VERIFY)

        verifier = self.deps.verifier_factory(self.clock.now(), self.valid_at)
        outcome = verifier.verify(
            run.candidate_facts,
            evidence=run.retrieval_results,
            tool_results=run.tool_results,
            snapshot_id=self.ids.new_id("fact"),
            contradiction_id=self.ids.new_id("contra"),
        )

        run = run.model_copy(
            update={
                "verified_facts": outcome.verified_facts,
                "contradictions": list(outcome.verified_facts.contradictions),
                "warnings": [*run.warnings, *outcome.warnings],
            }
        )
        run = await self.emitter.emit(
            run,
            EventType.VERIFICATION_COMPLETED,
            actor_type=ActorType.AGENT,
            actor_name="verifier",
            status=EventStatus.SUCCEEDED,
            data={
                "accepted": len(outcome.verified_facts.accepted()),
                "total": len(outcome.verified_facts.facts),
            },
        )
        run = await self._render_surface(
            run, headline="Estamos verificando la información.", node=NODE_VERIFY
        )
        run = await self.emitter.node_completed(run, NODE_VERIFY, duration_ms=0)
        return _graph(await self._persist(run, NODE_VERIFY))

    async def _estimate(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_ESTIMATE)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        estimator = self.deps.estimators.get(run.domain) if run.domain else None
        facts = run.verified_facts
        if estimator is None or facts is None:
            run = await self.emitter.node_completed(run, NODE_ESTIMATE, duration_ms=0)
            return _graph(await self._persist(run, NODE_ESTIMATE))

        run = await self.emitter.node_started(run, NODE_ESTIMATE)
        outcome = estimator.estimate(facts)
        run = run.model_copy(
            update={
                "estimate": outcome.estimate,
                "warnings": [*run.warnings, *outcome.warnings],
            }
        )
        run = await self._render_surface(
            run,
            headline="Estamos calculando costos y tiempos.",
            node=NODE_ESTIMATE,
            estimate=run.estimate,
        )
        run = await self.emitter.node_completed(run, NODE_ESTIMATE, duration_ms=0)
        return _graph(await self._persist(run, NODE_ESTIMATE))

    async def _merge(self, state: GraphState) -> GraphState:
        """Consolida y decide si hay una escritura que confirmar (`DIE-F1-085`)."""
        skipped = await self._skip_or_start(state, NODE_MERGE)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        run = await self.emitter.node_started(run, NODE_MERGE)

        action = self._pending_action(run)
        if action is not None:
            # El estado no se fija aquí: lo decide `finalize`, cuando ya se sabe
            # si la respuesta y la superficie llegaron a construirse.
            run = run.model_copy(update={"pending_action": action})
            run = await self.emitter.emit(
                run,
                EventType.RUN_WAITING_CONFIRMATION,
                actor_type=ActorType.SUPERVISOR,
                actor_name="supervisor",
                status=EventStatus.SUCCEEDED,
                data={"action_id": action.action_id, "tool": action.tool_name},
            )

        run = await self.emitter.node_completed(run, NODE_MERGE, duration_ms=0)
        return _graph(await self._persist(run, NODE_MERGE))

    async def _build_a2ui(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_BUILD_A2UI)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        builder = self.deps.surface_builder
        facts = run.verified_facts
        if builder is None or facts is None:
            run = await self.emitter.node_completed(run, NODE_BUILD_A2UI, duration_ms=0)
            return _graph(await self._persist(run, NODE_BUILD_A2UI))

        run = await self.emitter.node_started(run, NODE_BUILD_A2UI)
        # Solo se ofrece un botón mientras la confirmación siga pendiente: tras
        # ejecutarse (o cancelarse), reofrecerlo describiría un trámite que ya
        # no puede volver a dispararse.
        action = run.pending_action
        awaiting = (
            action
            if action is not None and action.status is ActionStatus.PENDING_CONFIRMATION
            else None
        )
        run = await self._render_surface(
            run,
            headline="Esto es lo que encontré",
            node=NODE_BUILD_A2UI,
            estimate=run.estimate,
            pending_action=awaiting,
        )
        surface = run.surface
        assert surface is not None

        validation = None
        if self.deps.surface_validator is not None:
            action_ids = frozenset({awaiting.action_id} if awaiting else set())
            validation = self.deps.surface_validator.validate(surface, run_action_ids=action_ids)

        if validation is not None and not validation.is_valid:
            # `DIE-F1-106`: una superficie inválida degrada a texto, nunca a nada.
            run = await self.emitter.emit(
                run,
                EventType.A2UI_VALIDATION_FAILED,
                actor_type=ActorType.SYSTEM,
                actor_name="a2ui_validator",
                status=EventStatus.FAILED,
                data={"errors": len(validation.errors)},
                error=NormalizedError.from_code(
                    ErrorCode.CONTRACT_INVALID, "la superficie no valida contra su catálogo"
                ),
            )
            run = run.model_copy(
                update={"surface": None, "fallback": self._fallback(run, "validation_failed")}
            )
        else:
            run = run.model_copy(update={"fallback": self._fallback(run, "channel_is_text_only")})
            run = await self.emitter.emit(
                run,
                EventType.A2UI_VALIDATED,
                actor_type=ActorType.SYSTEM,
                actor_name="a2ui_validator",
                status=EventStatus.SUCCEEDED,
                data={"surface_id": surface.surface_id},
            )

        run = await self.emitter.node_completed(run, NODE_BUILD_A2UI, duration_ms=0)
        return _graph(await self._persist(run, NODE_BUILD_A2UI))

    async def _write_answer(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_WRITE_ANSWER)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        facts = run.verified_facts
        if facts is None:
            run = await self.emitter.node_completed(run, NODE_WRITE_ANSWER, duration_ms=0)
            return _graph(await self._persist(run, NODE_WRITE_ANSWER))

        run = await self.emitter.node_started(run, NODE_WRITE_ANSWER)
        ledger = self._ledger(run)
        context = ModelCallContext(run_id=run.run_id, trace_id=run.trace_id, ledger=ledger)

        next_action = (
            "Confirma la acción para continuar." if run.pending_action is not None else None
        )
        outcome = await self.deps.writer.write(
            facts,
            context,
            channel=run.request.channel,
            profile=run.request.profile,
            warnings=tuple(run.warnings),
            next_action=next_action,
        )
        run = self._charge(run, outcome.invocations, ledger)
        run = await self._emit_model_events(run, outcome.invocations)
        run = run.model_copy(update={"answer": outcome.answer})
        run = await self.emitter.node_completed(run, NODE_WRITE_ANSWER, duration_ms=0)
        return _graph(await self._persist(run, NODE_WRITE_ANSWER))

    async def _finalize(self, state: GraphState) -> GraphState:
        skipped = await self._skip_or_start(state, NODE_FINALIZE)
        if skipped is not None:
            return _graph(skipped)

        run = state["run"]
        run = await self.emitter.node_started(run, NODE_FINALIZE)

        status = self._final_status(run)
        run = run.model_copy(
            update={
                "status": status,
                "metrics": run.metrics.model_copy(update={"duration_ms": self._elapsed_ms(run)}),
            }
        )
        run = await self.emitter.node_completed(run, NODE_FINALIZE, duration_ms=0)
        run = await self.emitter.emit(
            run,
            _TERMINAL_EVENT[status],
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        return _graph(await self._persist(run, NODE_FINALIZE))

    def _final_status(self, run: RunState) -> RunStatus:
        """Estado con el que termina esta pasada del grafo (`DIE-F1-091`).

        Un run con una acción sin confirmar **no ha terminado**: queda esperando
        a la persona. Marcarlo `succeeded` diría que el trámite está hecho
        cuando lo único que hay es un botón sin pulsar.
        """
        if run.pending_action is not None and run.pending_action.status in {
            ActionStatus.PENDING_CONFIRMATION,
        }:
            return RunStatus.WAITING_CONFIRMATION
        if any(result.status is ActionStatus.PARTIAL for result in run.action_results):
            return RunStatus.PARTIAL
        if any("no pudimos" in warning.lower() for warning in run.warnings):
            return RunStatus.PARTIAL
        return RunStatus.SUCCEEDED

    # -- acciones -----------------------------------------------------------

    def _pending_action(self, run: RunState) -> ActionRequest | None:
        """Construye la acción confirmable, si el recorrido la exige.

        Solo se propone cuando hay un hecho apto para escritura: sin evidencia
        que la sustente, ofrecer un botón de confirmar sería ofrecer un trámite
        que no podemos completar.
        """
        if run.domain is None or run.verified_facts is None:
            return None
        eligible = [fact for fact in run.verified_facts.accepted() if fact.write_eligible]
        if not eligible or run.verified_facts.has_blocking_contradiction():
            return None

        navigator = self.deps.navigators.get(run.domain)
        classification = run.classification
        if navigator is None or classification is None:
            return None
        write_tools = [
            intent.write_tool
            for detected in classification.intents
            if detected.domain is run.domain
            for intent in [navigator.manifest.intent(detected.intent)]
            if intent is not None and intent.write_tool is not None
        ]
        if not write_tools:
            return None

        tool_name = write_tools[0]
        definition = self.deps.catalog.definition(tool_name)
        if definition is None:
            return None

        return ActionRequest(
            action_id=self.ids.new_id("act"),
            run_id=run.run_id,
            tool_name=tool_name,
            input_schema_ref=definition.metadata.input_schema_ref,
            tool_version=definition.version,
            expected_version=1,
            parameters=_default_parameters(tool_name, run),
            requires_confirmation=True,
            consent=False,
            required_permission=f"{run.domain.value}:write",
            supporting_fact_ids=[fact.fact_id for fact in eligible[:5]],
        )

    def _fallback(self, run: RunState, reason: str) -> ChannelFallback:
        from nexo_a2ui import build_fallback

        assert run.verified_facts is not None
        return build_fallback(
            run.verified_facts,
            channel=run.request.channel,
            reason=reason,
            estimate=run.estimate,
            pending_action=run.pending_action,
            warnings=tuple(run.warnings),
        )

    def _navigator(self, run: RunState) -> DomainNavigator | None:
        return self.deps.navigators.get(run.domain) if run.domain else None

    async def _render_surface(
        self,
        run: RunState,
        *,
        headline: str,
        node: str,
        estimate: Estimate | None = None,
        pending_action: ActionRequest | None = None,
    ) -> RunState:
        """Actualiza `run.surface` con lo que ya se sabe en esta etapa.

        Cada llamada agrega un `updateDataModel` + `updateComponents` a la misma
        superficie (`previous=run.surface`) en vez de reemplazarla: la persona
        ve el checklist, luego el costo, luego la confirmación, sin esperar al
        último nodo para tener algo en pantalla (§5.8 `a2ui.generated`).
        """
        builder = self.deps.surface_builder
        facts = run.verified_facts
        if builder is None or facts is None:
            return run

        surface_id = run.surface.surface_id if run.surface is not None else self.ids.new_id("surf")
        surface = builder.build(
            facts,
            surface_id=surface_id,
            channel=run.request.channel,
            estimate=estimate,
            pending_action=pending_action,
            headline=headline,
            warnings=tuple(run.warnings),
            previous=run.surface,
        )
        run = run.model_copy(update={"surface": surface})
        return await self.emitter.emit(
            run,
            EventType.A2UI_GENERATED,
            actor_type=ActorType.SYSTEM,
            actor_name="a2ui_builder",
            status=EventStatus.SUCCEEDED,
            data={"surface_id": surface.surface_id, "stage": node},
        )

    # -- API pública ---------------------------------------------------------

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
        """Ejecuta el run hasta el final o hasta la confirmación pendiente."""
        state = self.initial_state(request)
        state = await self.emitter.emit(
            state,
            EventType.RUN_QUEUED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        state = state.model_copy(
            update={
                "metrics": state.metrics.model_copy(
                    update={"first_event_ms": self._elapsed_ms(state)}
                )
            }
        )
        final = cast(GraphState, await self._compiled.ainvoke({"run": state}))
        return RunResult.from_state(final["run"])

    async def resume(self, run_id: str, *, confirmed: bool = False) -> RunResult:
        """Reanuda desde el checkpoint (`DIE-F1-087`).

        Con `confirmed`, marca la acción pendiente como consentida y ejecuta el
        agente transaccional. Los nodos ya completados **no se reejecutan**: se
        registran como `skipped` en la traza.
        """
        state = await self.checkpoints.load(run_id)
        if state is None:
            raise LookupError(f"no hay checkpoint para el run {run_id!r}")
        if state.status in TERMINAL_RUN_STATUSES:
            return RunResult.from_state(state)

        state = await self.emitter.emit(
            state,
            EventType.CHECKPOINT_RESTORED,
            actor_type=ActorType.SYSTEM,
            actor_name="checkpoint_store",
            status=EventStatus.SUCCEEDED,
            data={"completed_nodes": list(state.completed_nodes)},
        )
        state = await self.emitter.emit(
            state,
            EventType.RUN_RESUMED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
            data={"confirmed": confirmed},
        )

        if confirmed and self._action_is_pending(state):
            state = await self._execute_action(state)

        state = state.model_copy(
            update={
                "status": RunStatus.RUNNING
                if state.status is RunStatus.WAITING_CONFIRMATION
                else state.status
            }
        )
        final = cast(GraphState, await self._compiled.ainvoke({"run": state}))
        return RunResult.from_state(final["run"])

    async def cancel(self, run_id: str) -> RunResult:
        """Cancela un run persistido sin ejecutar su acción pendiente."""
        state = await self.checkpoints.load(run_id)
        if state is None:
            raise LookupError(f"no hay checkpoint para el run {run_id!r}")
        if state.status in TERMINAL_RUN_STATUSES:
            return RunResult.from_state(state)

        pending_action = state.pending_action
        if pending_action is not None:
            pending_action = pending_action.model_copy(update={"status": ActionStatus.CANCELLED})
        state = state.model_copy(
            update={
                "status": RunStatus.CANCELLED,
                "pending_action": pending_action,
                "metrics": state.metrics.model_copy(
                    update={"duration_ms": self._elapsed_ms(state)}
                ),
            }
        )
        state = await self.emitter.emit(
            state,
            EventType.RUN_CANCELLED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
        )
        state = await self._persist(state, "cancel")
        return RunResult.from_state(state)

    @staticmethod
    def _action_is_pending(state: RunState) -> bool:
        """¿Queda una escritura por ejecutar?

        Una acción ya resuelta no se reintenta aunque llegue otra confirmación.
        La idempotencia del executor evitaría la segunda cita de todos modos,
        pero apoyarse solo en ella significaría que la protección vive en una
        capa y el desperdicio en otra: reconfirmar cinco veces enviaría cinco
        peticiones al sistema institucional.
        """
        action = state.pending_action
        return action is not None and action.status in {
            ActionStatus.PENDING_CONFIRMATION,
            ActionStatus.CONFIRMED,
        }

    async def _execute_action(self, state: RunState) -> RunState:
        """Ejecuta la acción confirmada mediante el agente transaccional."""
        action = state.pending_action
        facts = state.verified_facts
        assert action is not None
        assert facts is not None

        confirmed = action.model_copy(
            update={
                "consent": True,
                "status": ActionStatus.CONFIRMED,
                "idempotency_key": action.idempotency_key
                or f"idem-{state.run_id}-{action.action_id}",
            }
        )
        state = await self.emitter.emit(
            state,
            EventType.TOOL_AUTHORIZED,
            actor_type=ActorType.SUPERVISOR,
            actor_name="supervisor",
            status=EventStatus.SUCCEEDED,
            data={"action_id": confirmed.action_id, "tool": confirmed.tool_name},
        )

        outcome = await self.deps.transactional.execute(
            confirmed,
            facts=facts,
            identity=_permission_context(state),
            tool_call_id=self.ids.new_id("tc"),
            run_id=state.run_id,
            trace_id=state.trace_id,
        )

        state = await self.emitter.emit(
            state,
            EventType.TOOL_REPLAYED
            if outcome.action_result.idempotency_replayed
            else EventType.TOOL_COMPLETED,
            actor_type=ActorType.TOOL,
            actor_name=confirmed.tool_name,
            status=EventStatus.SUCCEEDED if outcome.succeeded else EventStatus.FAILED,
            data=dict(outcome.audit or {}),
            error=outcome.action_result.error if not outcome.succeeded else None,
        )
        return state.model_copy(
            update={
                "pending_action": confirmed.model_copy(
                    update={"status": outcome.action_result.status}
                ),
                "action_results": [*state.action_results, outcome.action_result],
                "warnings": [*state.warnings, *outcome.warnings],
                # `DIE-F1-088`: la redacción se rehace porque ahora hay folio que
                # comunicar; el resto de nodos siguen confirmados y se saltan.
                "completed_nodes": [
                    node
                    for node in state.completed_nodes
                    if node not in {NODE_WRITE_ANSWER, NODE_FINALIZE, NODE_BUILD_A2UI}
                ],
            }
        )


def _graph(run: RunState) -> GraphState:
    return {"run": run}


def _permission_context(run: RunState) -> ToolPermissionContext:
    identity = run.request.identity
    return ToolPermissionContext(
        user_id=identity.user_id,
        institution_id=identity.institution_id,
        roles=list(identity.roles),
        permissions=list(identity.permissions),
    )


def _default_parameters(tool_name: str, run: RunState) -> dict[str, JsonValue]:
    """Parámetros de demostración de la acción propuesta.

    En el MVP se conservan los valores ya consultados por las tools de lectura.
    Los respaldos de demo solo aplican cuando el escenario no entregó alguno;
    así la escritura nunca cambia silenciosamente de vehículo, predio o slot.
    """
    if tool_name == "vehiculos.reservar_cita":
        vehicle_ref: JsonValue = "veh_demo"
        slot_id: JsonValue = "slot_mod_centro_00"
        for proposal in run.proposed_tools:
            if proposal.name == "vehiculos.consultar_adeudo":
                proposed_ref = proposal.parameters.get("vehiculo_ref")
                if isinstance(proposed_ref, str):
                    vehicle_ref = proposed_ref
        for result in run.tool_results:
            if result.name != "vehiculos.buscar_citas":
                continue
            slots = result.data.get("slots")
            if not isinstance(slots, list):
                continue
            available = next(
                (
                    item
                    for item in slots
                    if isinstance(item, dict) and bool(item.get("disponible", True))
                ),
                None,
            )
            if available is not None and isinstance(available.get("slot_id"), str):
                slot_id = available["slot_id"]
        return {"slot_id": slot_id, "vehiculo_ref": vehicle_ref}

    if tool_name == "registro_civil.registrar_solicitud":
        return {"acta_ref": "acta_demo", "tipo": "correccion"}

    if tool_name == "ganaderia.registrar_vacuna":
        return {
            "animal_ref": "animal_demo_001",
            "vacuna": "vacuna_demo_autorizada",
            "fecha_aplicacion": "2026-07-30",
            "actor_ref": "actor_demo_productor",
            "regla_id": "sanidad_demo_2026_01",
        }

    parameters: dict[str, JsonValue] = {
        "giro": "taqueria",
        "predio_ref": "pred_demo",
        "tramite": "licencia_funcionamiento",
    }
    for proposal in run.proposed_tools:
        if proposal.name != "ayuntamiento.consultar_uso_suelo":
            continue
        for field_name in ("giro", "predio_ref"):
            value = proposal.parameters.get(field_name)
            if isinstance(value, str):
                parameters[field_name] = value
    return parameters


def channel_short_answer(run: RunState) -> str:
    """Representación breve para canales de texto (`DIE-F1-097`)."""
    if run.fallback is not None:
        return run.fallback.text
    return run.answer or ""


__all__ = [
    "NODES",
    "Channel",
    "GraphState",
    "MVPDependencies",
    "MVPGraph",
    "channel_short_answer",
]
