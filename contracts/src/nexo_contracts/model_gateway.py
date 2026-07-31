"""Contratos del gateway y el router de modelos (§5.6).

Los agentes solo conocen *aliases* y capacidades. Ningún contrato de este módulo
nombra un proveedor concreto ni un SDK: cambiar de proveedor debe ser un cambio
de configuración, no de código de agente (§2.3).
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import ModelDecisionReason, ModelHealth, ModelTaskKind, RiskLevel
from .errors import NormalizedError
from .ids import ModelInvocationId, RunId, TraceId
from .primitives import PositiveMillis, Score, UtcDatetime

ModelAlias = Annotated[
    str,
    Field(
        pattern=r"^[a-z][a-z0-9_]{2,40}$",
        description="Alias lógico como 'high_accuracy' o 'structured_small'.",
    ),
]


class ModelCapabilities(NexoModel):
    """Lo que un modelo puede hacer, en términos que el router entiende."""

    supports_structured_output: bool = False
    supports_vision: bool = False
    max_context_tokens: int = Field(ge=1, le=10_000_000)
    max_output_tokens: int = Field(ge=1, le=1_000_000)
    allows_sensitive_data: bool = Field(
        default=False,
        description="Si la política de datos permite enviarle contenido sensible.",
    )
    cost_per_1k_input_usd: float = Field(ge=0.0)
    cost_per_1k_output_usd: float = Field(ge=0.0)


class ModelPolicy(NexoModel):
    """Política de selección para un tipo de tarea (§4.4 de la arquitectura)."""

    task_kind: ModelTaskKind
    default_alias: ModelAlias
    escalation_alias: ModelAlias | None = None
    fallback_alias: ModelAlias | None = None
    max_attempts: int = Field(default=2, ge=1, le=5)
    min_accuracy_class: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Clase mínima de precisión; una tarea crítica no baja de aquí.",
    )
    allows_sensitive_data: bool = False
    policy_version: str = Field(max_length=40)


class ModelTask(NexoModel):
    """Solicitud de invocación tal como la formula un agente."""

    task_kind: ModelTaskKind
    requested_alias: ModelAlias
    output_schema_ref: str = Field(max_length=300)
    estimated_input_tokens: int = Field(ge=0, le=10_000_000)
    risk: RiskLevel = RiskLevel.LOW
    contains_sensitive_data: bool = False
    requires_vision: bool = False
    latency_budget_ms: PositiveMillis = 8000
    max_cost_usd: float = Field(default=0.05, ge=0.0)


class ModelCandidate(NexoModel):
    """Candidato considerado por el router, con su puntaje explicable."""

    alias: ModelAlias
    capabilities: ModelCapabilities
    health: ModelHealth = ModelHealth.UNKNOWN
    score: Score
    rejected_reason: str | None = Field(default=None, max_length=200)

    @property
    def is_eligible(self) -> bool:
        return self.rejected_reason is None and self.health is not ModelHealth.DOWN


class ModelDecision(NexoModel):
    """Decisión del router: qué se pidió, qué se usó y por qué (§5.6)."""

    requested_alias: ModelAlias
    selected_alias: ModelAlias
    reason: ModelDecisionReason
    considered: Annotated[list[ModelCandidate], Field(max_length=20)] = Field(default_factory=list)
    policy_version: str = Field(max_length=40)
    max_cost_usd: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _fallbacks_explain_themselves(self) -> Self:
        if (
            self.selected_alias != self.requested_alias
            and self.reason is ModelDecisionReason.POLICY_DEFAULT
        ):
            raise ValueError(
                f"el router cambió de '{self.requested_alias}' a '{self.selected_alias}' "
                f"declarando 'policy_default'; todo cambio de alias exige un motivo explícito"
            )
        return self


class ModelInvocation(NexoModel):
    """Registro de una invocación concreta (§5.6).

    Es la unidad de trazabilidad de costo del sistema: el gate de rendimiento
    exige que el 100% de los runs registren costo y tokens.
    """

    invocation_id: ModelInvocationId
    run_id: RunId
    trace_id: TraceId
    decision: ModelDecision
    attempt: int = Field(ge=1, le=5)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    duration_ms: PositiveMillis
    schema_valid: bool = True
    started_at: UtcDatetime
    error: NormalizedError | None = None

    @model_validator(mode="after")
    def _invalid_output_is_recorded_as_error(self) -> Self:
        if not self.schema_valid and self.error is None:
            raise ValueError(
                "una invocación con salida inválida debe adjuntar el error normalizado "
                "que el router usará para decidir el fallback"
            )
        return self
