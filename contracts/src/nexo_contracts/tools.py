"""Contratos de MCP: metadata, invocación, resultado y ciclo de vida (§5.4).

Aquí vive el invariante más importante del sistema: una tool de escritura no
puede invocarse sin confirmación explícita ni `idempotency_key`, y un resultado
de escritura solo cuenta como éxito si trae un identificador verificable.
"""

from __future__ import annotations

import re
from typing import Annotated, Self

from pydantic import Field, JsonValue, model_validator

from .base import FrozenNexoModel, NexoModel
from .enums import (
    Domain,
    ErrorCode,
    IntegrationState,
    Outcome,
    RiskLevel,
    ToolCallStatus,
    ToolMode,
)
from .errors import NormalizedError
from .ids import (
    ActionId,
    IdempotencyKey,
    IntegrationId,
    RunId,
    ToolCallId,
    TraceId,
    UserId,
)
from .primitives import PositiveMillis, SemanticVersion, UtcDatetime
from .safety import SafePayload

_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{1,30}\.[a-z][a-z0-9_]{1,60}$")

ToolName = Annotated[
    str,
    Field(
        max_length=95,
        description="Nombre `dominio.verbo_objeto`, por ejemplo 'vehiculos.reservar_cita'.",
    ),
]

SchemaRef = Annotated[
    str,
    Field(
        pattern=r"^contracts://[a-z0-9_\-./]+\.v\d+$",
        max_length=300,
        description="Referencia inmutable a un JSON Schema publicado en `contracts`.",
    ),
]

SecretRef = Annotated[
    str,
    Field(
        pattern=r"^secret://[a-z0-9_\-./]+$",
        max_length=300,
        description="Referencia a un secreto resuelto fuera del repositorio (`DIE-F0-033`).",
    ),
]


_DOMAIN_TOOL_PREFIX: dict[Domain, str] = {
    Domain.VEHICULOS: "vehiculos",
    # El dominio `ayuntamiento_empresas` usa el prefijo corto `ayuntamiento`, fijado por
    # la arquitectura §7.10 y por los nombres de tool del MVP (`DIE-F1-064` y ss.).
    Domain.AYUNTAMIENTO_EMPRESAS: "ayuntamiento",
    Domain.REGISTRO_CIVIL: "registro_civil",
    Domain.SALUD: "salud",
    Domain.GANADERIA: "ganaderia",
}


class ToolMetadata(NexoModel):
    """Descriptor versionado de una tool (§5.4).

    Los valores por defecto niegan: modo lectura, riesgo bajo, sin roles
    permitidos. Una tool mal declarada no es invocable por nadie (`DIE-F0-032`).
    """

    name: ToolName
    version: SemanticVersion
    domain: Domain
    mode: ToolMode = ToolMode.READ
    risk: RiskLevel = RiskLevel.LOW
    allowed_roles: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    requires_confirmation: bool = False
    requires_idempotency_key: bool = False
    timeout_ms: PositiveMillis = 5000
    max_attempts: int = Field(default=1, ge=1, le=5)
    input_schema_ref: SchemaRef
    output_schema_ref: SchemaRef
    is_mock: bool = True
    description: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _validate_name(self) -> Self:
        if not _TOOL_NAME.match(self.name):
            raise ValueError(
                f"nombre de tool inválido: {self.name!r}; se espera 'dominio.verbo_objeto' "
                f"en snake_case"
            )
        prefix = self.name.split(".", 1)[0]
        expected = _DOMAIN_TOOL_PREFIX[self.domain]
        if prefix != expected:
            raise ValueError(
                f"la tool {self.name!r} declara el dominio '{self.domain.value}' pero usa el "
                f"prefijo '{prefix}'; se esperaba '{expected}'"
            )
        return self

    @model_validator(mode="after")
    def _writes_are_confirmed_and_idempotent(self) -> Self:
        """Una tool de escritura sin confirmación e idempotencia no puede registrarse."""
        if self.mode is ToolMode.WRITE:
            if not self.requires_confirmation:
                raise ValueError(
                    f"la tool de escritura {self.name!r} debe exigir confirmación explícita"
                )
            if not self.requires_idempotency_key:
                raise ValueError(
                    f"la tool de escritura {self.name!r} debe exigir idempotency_key"
                )
            if self.max_attempts != 1:
                raise ValueError(
                    f"la tool de escritura {self.name!r} declara max_attempts="
                    f"{self.max_attempts}; una escritura nunca se reintenta automáticamente"
                )
        return self


class ToolPermissionContext(NexoModel):
    """Identidad y permiso efectivo con el que se evalúa una invocación."""

    user_id: UserId
    institution_id: str = Field(max_length=70)
    roles: Annotated[list[str], Field(max_length=20)]
    permissions: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)


class ToolCall(NexoModel):
    """Invocación tipada de una tool (§5.4)."""

    tool_call_id: ToolCallId
    name: ToolName
    version: SemanticVersion
    run_id: RunId
    trace_id: TraceId
    context: ToolPermissionContext
    parameters: SafePayload
    deadline_ms: PositiveMillis = 5000
    action_id: ActionId | None = Field(
        default=None, description="Presente solo cuando la invocación ejecuta una acción."
    )
    idempotency_key: IdempotencyKey | None = None
    confirmed: bool = Field(
        default=False,
        description="Consentimiento explícito de la persona usuaria para esta acción.",
    )
    mode: ToolMode = ToolMode.READ

    @model_validator(mode="after")
    def _writes_carry_consent_and_key(self) -> Self:
        if self.mode is not ToolMode.WRITE:
            return self
        missing = []
        if not self.confirmed:
            missing.append("confirmed")
        if self.idempotency_key is None:
            missing.append("idempotency_key")
        if self.action_id is None:
            missing.append("action_id")
        if missing:
            raise ValueError(
                f"la invocación de escritura {self.name!r} no puede construirse sin "
                f"{missing}; ninguna escritura ocurre sin acción confirmada e idempotente"
            )
        return self


class ToolError(NexoModel):
    """Error normalizado de una tool (§5.4)."""

    error: NormalizedError
    provider: str = Field(default="mock", max_length=100)
    safe_details: SafePayload

    @property
    def code(self) -> ErrorCode:
        return self.error.code

    @property
    def outcome(self) -> Outcome:
        return self.error.outcome


class ToolConfirmation(NexoModel):
    """Comprobante verificable de una escritura.

    Sin folio, UUID o identificador equivalente no hay éxito: el resultado se
    degrada a `partial` (`DIE-F1-078`).
    """

    identifier: str = Field(
        min_length=3,
        max_length=120,
        description="Folio, UUID o identificador devuelto por el sistema destino.",
    )
    identifier_kind: str = Field(default="folio", max_length=40)
    is_mock: bool = True
    issued_at: UtcDatetime


class ToolResult(NexoModel):
    """Resultado de una invocación (§5.4)."""

    tool_call_id: ToolCallId
    name: ToolName
    status: ToolCallStatus
    data: dict[str, JsonValue] = Field(default_factory=dict)
    confirmation: ToolConfirmation | None = None
    provider: str = Field(default="mock", max_length=100)
    duration_ms: PositiveMillis
    idempotency_replayed: bool = False
    is_mock: bool = True
    error: ToolError | None = None

    @model_validator(mode="after")
    def _status_matches_payload(self) -> Self:
        if self.status is ToolCallStatus.SUCCEEDED and self.error is not None:
            raise ValueError("un resultado exitoso no puede transportar un error")
        if self.status is not ToolCallStatus.SUCCEEDED and self.error is None:
            raise ValueError(
                f"el resultado con estado '{self.status.value}' debe incluir un error "
                f"normalizado para que el supervisor pueda decidir"
            )
        return self


class IntegrationDraft(NexoModel):
    """Borrador de integración del MCP Mapper (§5.4, ciclo de Fase 3)."""

    integration_id: IntegrationId
    state: IntegrationState = IntegrationState.DRAFT
    title: str = Field(max_length=200)
    domain: Domain
    proposed_tools: Annotated[list[ToolMetadata], Field(max_length=50)] = Field(
        default_factory=list
    )
    auth_secret_ref: SecretRef | None = None
    egress_allowlist: Annotated[list[str], Field(max_length=50)] = Field(default_factory=list)
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _drafts_are_never_visible_to_agents(self) -> Self:
        if self.state in {IntegrationState.DRAFT, IntegrationState.PARSED} and any(
            not tool.is_mock for tool in self.proposed_tools
        ):
            raise ValueError(
                "una integración en borrador no puede proponer tools no-mock: "
                "draft y parsed nunca son visibles para los agentes"
            )
        return self


class MapperValidation(NexoModel):
    """Resultado de validar un borrador contra schemas y políticas."""

    integration_id: IntegrationId
    passed: bool
    findings: Annotated[list[str], Field(max_length=200)] = Field(default_factory=list)
    blocked_reasons: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    validated_at: UtcDatetime

    @model_validator(mode="after")
    def _failure_needs_reason(self) -> Self:
        if not self.passed and not self.blocked_reasons:
            raise ValueError("una validación fallida debe declarar al menos un motivo de bloqueo")
        return self


class ControlledTestResult(NexoModel):
    """Prueba controlada con datos sintéticos en sandbox."""

    integration_id: IntegrationId
    tool_name: ToolName
    passed: bool
    used_synthetic_data: bool = True
    request_summary: SafePayload
    response_summary: SafePayload
    error: NormalizedError | None = None
    tested_at: UtcDatetime

    @model_validator(mode="after")
    def _real_data_is_never_allowed(self) -> Self:
        if not self.used_synthetic_data:
            raise ValueError(
                "una prueba controlada debe ejecutarse con datos sintéticos; "
                "no se admite tráfico con datos reales en el ciclo del Mapper"
            )
        return self


class Approval(NexoModel):
    """Aprobación humana con actor, momento y versión aprobada."""

    integration_id: IntegrationId
    approved_by: UserId
    approved_at: UtcDatetime
    diff_digest: str = Field(max_length=200)
    version: SemanticVersion
    notes: str = Field(default="", max_length=1000)


class PublishedToolVersion(FrozenNexoModel):
    """Versión inmutable publicada en el registry (§5.4)."""

    integration_id: IntegrationId
    metadata: ToolMetadata
    state: IntegrationState = IntegrationState.PUBLISHED
    published_at: UtcDatetime
    approved_by: UserId
    supersedes: SemanticVersion | None = None

    @model_validator(mode="after")
    def _only_terminal_states_are_publishable(self) -> Self:
        if self.state not in {IntegrationState.PUBLISHED, IntegrationState.DEPRECATED}:
            raise ValueError(
                f"una versión publicada no puede estar en estado '{self.state.value}'; "
                f"solo 'published' o 'deprecated' son válidos aquí"
            )
        return self
