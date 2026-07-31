"""Contratos de ejecución (§5.1).

`RunState` es el corazón del sistema y carga la invariante de `DIE-F0-015`: es
serializable de punta a punta, no contiene clientes, handles ni corrutinas, y no
transporta secretos. Eso no se logra con disciplina sino con tipos: todos los
campos de forma libre son `SafePayload`, que solo admite JSON puro sin claves de
secreto ni PII directa.

`RunResult` se construye desde el estado dejando fuera los campos internos, de
modo que un consumidor externo nunca vea el andamiaje de la ejecución
(`DIE-F0-044`).
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .a2ui import A2UIAction, A2UISurface, ChannelFallback
from .base import CONTRACTS_SCHEMA_VERSION, NexoModel
from .classification import Classification
from .enums import (
    ActionStatus,
    AgentName,
    Audience,
    Channel,
    Domain,
    RunStatus,
    TaskStatus,
    ToolMode,
)
from .errors import NormalizedError
from .estimation import Estimate
from .evaluation import SelfCheckResult
from .events import RunEvent
from .facts import CandidateFact, Contradiction, Deduction, SourceCitation, VerifiedFacts
from .ids import (
    ActionId,
    ConversationId,
    EventId,
    FactId,
    IdempotencyKey,
    InstitutionId,
    RunId,
    SourceId,
    TaskId,
    ToolCallId,
    TraceId,
    UserId,
)
from .model_gateway import ModelAlias, ModelInvocation
from .primitives import Confidence, PositiveMillis, SemanticVersion, Slug, UtcDatetime
from .rag import RetrievalResult
from .safety import SafePayload
from .tools import ToolName, ToolResult


class Identity(NexoModel):
    """Identidad y permisos efectivos con los que corre la ejecución."""

    user_id: UserId
    institution_id: InstitutionId
    roles: Annotated[list[str], Field(min_length=1, max_length=20)]
    permissions: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)


class Profile(NexoModel):
    audience: Audience = Audience.CITIZEN
    locale: str = Field(default="es-MX", pattern=r"^[a-z]{2}-[A-Z]{2}$")


class Budgets(NexoModel):
    """Presupuestos del run (`DIE-F0-034`).

    Se aplican en el supervisor y en cada nodo: antes de invocar un modelo o una
    tool se comprueba lo que queda, no después.
    """

    deadline_ms: PositiveMillis = 20000
    max_cost_usd: float = Field(default=0.20, ge=0.0, le=100.0)
    max_tokens: int = Field(default=200_000, ge=0)
    max_attempts_per_agent: int = Field(default=2, ge=1, le=5)
    max_concurrency: int = Field(default=2, ge=1, le=10)


class DeducedContextItem(NexoModel):
    """Dato de contexto inferido antes o durante el run."""

    key: Slug
    deduction: Deduction


class RunRequest(NexoModel):
    """Entrada del núcleo (§5.1). Es lo único que el backend entrega al supervisor."""

    run_id: RunId
    trace_id: TraceId
    conversation_id: ConversationId
    user_message: str = Field(min_length=1, max_length=8000)
    channel: Channel
    identity: Identity
    profile: Profile = Field(default_factory=Profile)
    deduced_context: Annotated[list[DeducedContextItem], Field(max_length=50)] = Field(
        default_factory=list
    )
    budgets: Budgets = Field(default_factory=Budgets)
    received_at: UtcDatetime


class AgentTask(NexoModel):
    """Tarea que el supervisor delega a un agente (§5.1).

    `allowed_sources` y `allowed_tools` son allowlists cerradas: el agente no
    puede ampliarlas, y el executor las revalida por su cuenta.
    """

    task_id: TaskId
    run_id: RunId
    agent: AgentName
    objective: str = Field(max_length=500)
    input_refs: Annotated[list[FactId], Field(max_length=200)] = Field(default_factory=list)
    allowed_sources: Annotated[list[SourceId], Field(max_length=200)] = Field(default_factory=list)
    allowed_tools: Annotated[list[ToolName], Field(max_length=50)] = Field(default_factory=list)
    deadline_ms: PositiveMillis = 6000
    model_policy: ModelAlias = "general"
    attempt: int = Field(default=1, ge=1, le=5)
    max_cost_usd: float = Field(default=0.05, ge=0.0)

    @model_validator(mode="after")
    def _non_transactional_agents_get_no_write_budget(self) -> Self:
        """Solo el agente transaccional puede recibir tools de escritura (§2.3).

        La comprobación por nombre es una primera barrera; el executor revalida
        el modo real de la tool contra el registry.
        """
        if self.agent is AgentName.TRANSACTIONAL:
            return self
        if self.agent is AgentName.WRITER and (self.allowed_sources or self.allowed_tools):
            raise ValueError(
                "el redactor es un agente cerrado: no puede recibir fuentes ni tools (`DIE-F1-094`)"
            )
        return self


class ProposedToolCall(NexoModel):
    """Tool que un agente propone, sin ejecutarla."""

    name: ToolName
    mode: ToolMode = ToolMode.READ
    rationale: str = Field(max_length=300)
    parameters: SafePayload


class AgentResult(NexoModel):
    """Salida de un agente (§5.1)."""

    task_id: TaskId
    agent: AgentName
    status: TaskStatus
    facts: Annotated[list[CandidateFact], Field(max_length=300)] = Field(default_factory=list)
    citations: Annotated[list[SourceCitation], Field(max_length=200)] = Field(default_factory=list)
    proposed_tools: Annotated[list[ProposedToolCall], Field(max_length=20)] = Field(
        default_factory=list
    )
    contradictions: Annotated[list[Contradiction], Field(max_length=50)] = Field(
        default_factory=list
    )
    warnings: Annotated[list[str], Field(max_length=50)] = Field(default_factory=list)
    self_check: SelfCheckResult
    confidence: Confidence = 1.0
    error: NormalizedError | None = None

    @model_validator(mode="after")
    def _failures_are_explained(self) -> Self:
        if self.status is TaskStatus.FAILED and self.error is None:
            raise ValueError(
                f"el agente {self.agent.value!r} devolvió 'failed' sin error normalizado"
            )
        return self

    @model_validator(mode="after")
    def _only_transactional_proposes_writes(self) -> Self:
        if self.agent is AgentName.TRANSACTIONAL:
            return self
        writes = [tool.name for tool in self.proposed_tools if tool.mode is ToolMode.WRITE]
        if writes:
            raise ValueError(
                f"el agente {self.agent.value!r} propone tools de escritura {writes}; "
                f"solo el agente transaccional puede solicitarlas"
            )
        return self


class ActionRequest(NexoModel):
    """Acción pendiente de confirmación (§5.1).

    Se persiste en el checkpoint antes del interrupt, con el schema y la versión
    esperada, para que la reanudación no dependa de nada en memoria
    (`DIE-F1-086`).
    """

    action_id: ActionId
    run_id: RunId
    tool_name: ToolName
    input_schema_ref: str = Field(max_length=300)
    tool_version: SemanticVersion
    expected_version: int = Field(ge=1)
    parameters: SafePayload
    requires_confirmation: bool = True
    consent: bool = False
    idempotency_key: IdempotencyKey | None = None
    required_permission: str = Field(max_length=120)
    status: ActionStatus = ActionStatus.PENDING_CONFIRMATION
    supporting_fact_ids: Annotated[list[FactId], Field(max_length=100)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def _confirmed_actions_are_complete(self) -> Self:
        """Confirmar exige consentimiento e idempotencia, en ese mismo momento."""
        if self.status in {
            ActionStatus.PENDING_CONFIRMATION,
            ActionStatus.CANCELLED,
        }:
            return self
        if self.requires_confirmation and not self.consent:
            raise ValueError(
                f"la acción {self.action_id!r} avanzó a '{self.status.value}' sin "
                f"consentimiento explícito"
            )
        if self.idempotency_key is None:
            raise ValueError(
                f"la acción {self.action_id!r} avanzó a '{self.status.value}' sin "
                f"idempotency_key; reanudar el run podría duplicar el efecto"
            )
        return self

    def to_a2ui_action(self, *, label: str) -> A2UIAction:
        """Proyecta la acción a su forma A2UI, sin exponer parámetros ni permisos."""
        return A2UIAction(
            action_id=self.action_id,
            tool_name=self.tool_name,
            input_schema_ref=self.input_schema_ref,
            expected_version=self.expected_version,
            requires_confirmation=self.requires_confirmation,
            label=label,
        )


class ActionResult(NexoModel):
    """Resultado de ejecutar una acción confirmada (§5.1)."""

    action_id: ActionId
    status: ActionStatus
    tool_call_id: ToolCallId | None = None
    tool_result: ToolResult | None = None
    idempotency_replayed: bool = False
    error: NormalizedError | None = None

    @model_validator(mode="after")
    def _success_requires_verifiable_confirmation(self) -> Self:
        """Sin folio verificable no hay éxito (`DIE-F1-078`)."""
        if self.status is not ActionStatus.SUCCEEDED:
            return self
        if self.tool_result is None or self.tool_result.confirmation is None:
            raise ValueError(
                f"la acción {self.action_id!r} se declara exitosa sin identificador "
                f"verificable; un resultado sin folio se reporta como 'partial'"
            )
        return self


class RunMetrics(NexoModel):
    """Métricas obligatorias del run. El gate exige que el 100% las registre."""

    duration_ms: PositiveMillis = 0
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    total_input_tokens: int = Field(default=0, ge=0)
    total_output_tokens: int = Field(default=0, ge=0)
    model_invocation_count: int = Field(default=0, ge=0)
    tool_call_count: int = Field(default=0, ge=0)
    retrieval_count: int = Field(default=0, ge=0)
    question_count: int = Field(default=0, ge=0)
    first_event_ms: PositiveMillis | None = None


class RunState(NexoModel):
    """Estado serializable del run (§5.1, `DIE-F0-015`).

    Los campos marcados como internos existen para orquestar (reintentos, nodos
    completados, invocaciones de modelo) y no forman parte de ninguna respuesta:
    `model_dump_wire()` los elimina y `RunResult` no los lee.
    """

    schema_revision: str = Field(default=CONTRACTS_SCHEMA_VERSION, max_length=10)
    run_id: RunId
    trace_id: TraceId
    conversation_id: ConversationId
    status: RunStatus = RunStatus.QUEUED
    request: RunRequest
    created_at: UtcDatetime
    updated_at: UtcDatetime

    domain: Domain | None = None
    classification: Classification | None = Field(
        default=None,
        json_schema_extra={"nexo_visibility": "internal"},
        description=(
            "Clasificación persistida; reanudar después del nodo classify no depende "
            "de memoria del proceso."
        ),
    )
    tasks: Annotated[list[AgentTask], Field(max_length=200)] = Field(default_factory=list)
    candidate_facts: Annotated[list[CandidateFact], Field(max_length=500)] = Field(
        default_factory=list,
        json_schema_extra={"nexo_visibility": "internal"},
    )
    verified_facts: VerifiedFacts | None = None
    contradictions: Annotated[list[Contradiction], Field(max_length=100)] = Field(
        default_factory=list
    )
    estimate: Estimate | None = None
    pending_action: ActionRequest | None = None
    action_results: Annotated[list[ActionResult], Field(max_length=50)] = Field(
        default_factory=list
    )
    surface: A2UISurface | None = None
    fallback: ChannelFallback | None = None
    answer: str | None = Field(default=None, max_length=20000)
    warnings: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    questions: Annotated[list[str], Field(max_length=5)] = Field(default_factory=list)
    metrics: RunMetrics = Field(default_factory=RunMetrics)
    error: NormalizedError | None = None

    event_cursor: int = Field(
        default=0,
        ge=0,
        description="Última `sequence` emitida; el siguiente evento usa `event_cursor + 1`.",
    )
    last_event_id: EventId | None = None
    completed_nodes: Annotated[list[str], Field(max_length=100)] = Field(
        default_factory=list,
        json_schema_extra={"nexo_visibility": "internal"},
        description="Nodos ya confirmados; reanudar no los reejecuta (`DIE-F0-042`).",
    )
    attempts: dict[str, int] = Field(
        default_factory=dict,
        json_schema_extra={"nexo_visibility": "internal"},
    )
    model_invocations: Annotated[list[ModelInvocation], Field(max_length=200)] = Field(
        default_factory=list,
        json_schema_extra={"nexo_visibility": "internal"},
    )
    retrieval_results: Annotated[list[RetrievalResult], Field(max_length=100)] = Field(
        default_factory=list,
        json_schema_extra={"nexo_visibility": "internal"},
        description="Evidencia exacta del run, necesaria para reanudar antes de verify.",
    )
    proposed_tools: Annotated[list[ProposedToolCall], Field(max_length=20)] = Field(
        default_factory=list,
        json_schema_extra={"nexo_visibility": "internal"},
        description="Tools de lectura propuestas y filtradas por el navegador.",
    )
    tool_results: Annotated[list[ToolResult], Field(max_length=100)] = Field(
        default_factory=list,
        json_schema_extra={"nexo_visibility": "internal"},
        description="Resultados de lectura persistidos para reanudar antes de verify.",
    )
    policy_version: str = Field(default="unset", max_length=40)
    catalog_version: str = Field(default="unset", max_length=80)
    active_skill_id: str | None = Field(default=None, max_length=80)
    active_skill_version: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _waiting_confirmation_has_a_pending_action(self) -> Self:
        if self.status is RunStatus.WAITING_CONFIRMATION and self.pending_action is None:
            raise ValueError(
                "el run está en 'waiting_confirmation' sin acción pendiente persistida; "
                "la reanudación no tendría qué confirmar"
            )
        return self

    @model_validator(mode="after")
    def _terminal_failures_carry_an_error(self) -> Self:
        if self.status is RunStatus.FAILED and self.error is None:
            raise ValueError("un run fallido debe registrar el error normalizado que lo detuvo")
        return self

    def assert_serializable(self) -> None:
        """Verifica de forma explícita que el estado puede ir a un checkpoint.

        Los tipos ya impiden guardar un objeto vivo, pero esta comprobación deja
        el invariante escrito y ejecutable donde el lector lo busca.
        """
        self.model_dump_json()

    def has_completed(self, node: str) -> bool:
        return node in self.completed_nodes


class RunResult(NexoModel):
    """Salida del núcleo (§5.1).

    Se construye desde `RunState` omitiendo todo lo interno: hechos candidatos
    sin verificar, nodos completados, reintentos e invocaciones de modelo no
    salen de la orquestación.
    """

    run_id: RunId
    trace_id: TraceId
    status: RunStatus
    verified_facts: VerifiedFacts | None = None
    estimate: Estimate | None = None
    answer: str | None = Field(default=None, max_length=20000)
    surface: A2UISurface | None = None
    fallback: ChannelFallback | None = None
    sources: Annotated[list[SourceCitation], Field(max_length=200)] = Field(default_factory=list)
    available_actions: Annotated[list[A2UIAction], Field(max_length=20)] = Field(
        default_factory=list
    )
    warnings: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    questions: Annotated[list[str], Field(max_length=5)] = Field(default_factory=list)
    metrics: RunMetrics = Field(default_factory=RunMetrics)
    error: NormalizedError | None = None
    catalog_version: str = Field(default="unset", max_length=80)
    skill_id: str | None = Field(default=None, max_length=80)
    skill_version: str | None = Field(default=None, max_length=40)

    @classmethod
    def from_state(cls, state: RunState, *, action_label: str = "Confirmar") -> RunResult:
        """Proyección explícita de estado a resultado.

        Deliberadamente enumera campo por campo en lugar de copiar el estado: si
        mañana alguien añade un campo interno a `RunState`, no se filtra solo por
        haberlo declarado.
        """
        sources: list[SourceCitation] = []
        if state.verified_facts is not None:
            seen: set[tuple[str, str]] = set()
            for fact in state.verified_facts.facts:
                for citation in fact.citations:
                    key = (citation.source_id, citation.fragment_id)
                    if key not in seen:
                        seen.add(key)
                        sources.append(citation)

        actions: list[A2UIAction] = []
        if (
            state.pending_action is not None
            and state.pending_action.status is ActionStatus.PENDING_CONFIRMATION
        ):
            actions.append(state.pending_action.to_a2ui_action(label=action_label))

        return cls(
            run_id=state.run_id,
            trace_id=state.trace_id,
            status=state.status,
            verified_facts=state.verified_facts,
            estimate=state.estimate,
            answer=state.answer,
            surface=state.surface,
            fallback=state.fallback,
            sources=sources,
            available_actions=actions,
            warnings=list(state.warnings),
            questions=list(state.questions),
            metrics=state.metrics,
            error=state.error,
            catalog_version=state.catalog_version,
            skill_id=state.active_skill_id,
            skill_version=state.active_skill_version,
        )


class RunSnapshot(NexoModel):
    """Estado más eventos, para reproducir una ejecución completa por `trace_id`."""

    state: RunState
    events: Annotated[list[RunEvent], Field(max_length=10_000)] = Field(default_factory=list)
