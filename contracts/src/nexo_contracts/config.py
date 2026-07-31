"""Schemas de configuración versionada (`DIE-F0-031`–`DIE-F0-037`).

`config/README.md` establece que `contracts` define los schemas y `config` los
datos. Aquí están los schemas.

Todos los defaults **niegan**: sin escrituras, sin proveedores desconocidos, sin
tools sin versión y sin reintentos. Una configuración que no dice nada es una
configuración que no autoriza nada. Y la configuración nunca contiene secretos:
solo referencias `secret://` que se resuelven fuera del repositorio.
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import AgentName, Domain, ErrorCode, ToolMode
from .execution import Budgets
from .model_gateway import ModelAlias, ModelCapabilities, ModelPolicy
from .primitives import PositiveMillis, SemanticVersion, Slug
from .tools import SecretRef, ToolName

ConfigVersion = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,39}$")]


class ProviderRef(NexoModel):
    """Apunta a un proveedor y un modelo concretos, sin transportar credenciales."""

    provider: Slug
    model: str = Field(max_length=200)
    api_key_ref: SecretRef | None = Field(
        default=None,
        description="Referencia al secreto. Nunca el valor (`DIE-F0-033`).",
    )
    base_url_ref: SecretRef | None = None


class ModelAliasConfig(NexoModel):
    """Un alias lógico resuelto a un proveedor. Los agentes solo conocen el alias."""

    alias: ModelAlias
    provider_ref: ProviderRef
    capabilities: ModelCapabilities
    enabled: bool = True


class ModelRouterConfig(NexoModel):
    """`config/model_router.yaml` (`DIE-F0-031`)."""

    version: ConfigVersion
    allowed_providers: Annotated[list[Slug], Field(min_length=1, max_length=20)]
    aliases: Annotated[list[ModelAliasConfig], Field(min_length=1, max_length=50)]
    policies: Annotated[list[ModelPolicy], Field(min_length=1, max_length=30)]
    offline_alias: ModelAlias = Field(
        description="Alias del perfil offline; la demo sin red debe poder resolverlo.",
    )

    @model_validator(mode="after")
    def _providers_are_declared(self) -> Self:
        unknown = sorted(
            {
                entry.provider_ref.provider
                for entry in self.aliases
                if entry.provider_ref.provider not in self.allowed_providers
            }
        )
        if unknown:
            raise ValueError(
                f"proveedores no declarados en allowed_providers: {unknown}; un proveedor "
                f"desconocido se niega por defecto"
            )
        return self

    @model_validator(mode="after")
    def _policy_aliases_resolve(self) -> Self:
        known = {entry.alias for entry in self.aliases}
        dangling: list[str] = []
        for policy in self.policies:
            for candidate in (
                policy.default_alias,
                policy.escalation_alias,
                policy.fallback_alias,
            ):
                if candidate is not None and candidate not in known:
                    dangling.append(f"{policy.task_kind.value}:{candidate}")
        if self.offline_alias not in known:
            dangling.append(f"offline_alias:{self.offline_alias}")
        if dangling:
            raise ValueError(f"alias referenciados que no existen: {sorted(set(dangling))}")
        return self

    @model_validator(mode="after")
    def _aliases_are_unique(self) -> Self:
        seen = [entry.alias for entry in self.aliases]
        if len(seen) != len(set(seen)):
            raise ValueError("hay aliases duplicados en el router de modelos")
        return self


class ToolRegistryEntry(NexoModel):
    """Una tool registrada, siempre con versión explícita (`DIE-F0-032`)."""

    name: ToolName
    version: SemanticVersion
    domain: Domain
    mode: ToolMode = ToolMode.READ
    enabled: bool = False
    institution_id: str | None = Field(
        default=None,
        max_length=70,
        description="Nulo significa disponible para toda institución.",
    )


class ToolRegistryConfig(NexoModel):
    """`config/tool_registry.yaml`."""

    version: ConfigVersion
    tools: Annotated[list[ToolRegistryEntry], Field(max_length=200)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _versions_are_unique(self) -> Self:
        keys = [(entry.name, entry.version) for entry in self.tools]
        if len(keys) != len(set(keys)):
            raise ValueError("hay entradas duplicadas de la misma tool y versión")
        return self


class PermissionRule(NexoModel):
    """Una celda de la matriz institución × rol × dominio × tool × operación."""

    institution_id: str = Field(max_length=70)
    role: str = Field(max_length=40)
    domain: Domain
    tool: ToolName | None = Field(
        default=None, description="Nulo aplica a todas las tools del dominio."
    )
    operations: Annotated[list[ToolMode], Field(min_length=1, max_length=3)]
    allow: bool = False


class PermissionsConfig(NexoModel):
    """`config/permissions.yaml`. Deniega por defecto."""

    version: ConfigVersion
    default_allow: bool = Field(
        default=False,
        description="Debe permanecer en falso: sin regla explícita, no hay permiso.",
    )
    rules: Annotated[list[PermissionRule], Field(max_length=500)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _default_never_allows(self) -> Self:
        if self.default_allow:
            raise ValueError(
                "default_allow debe ser falso: un permiso implícito convierte la matriz de "
                "autorización en decorativa"
            )
        return self

    @model_validator(mode="after")
    def _writes_are_granted_one_by_one(self) -> Self:
        """Una regla que concede escritura debe nombrar la tool exacta."""
        for rule in self.rules:
            if rule.allow and ToolMode.WRITE in rule.operations and rule.tool is None:
                raise ValueError(
                    f"la regla para el rol {rule.role!r} en {rule.domain.value} concede "
                    f"escritura sobre todas las tools del dominio; una escritura se autoriza "
                    f"tool por tool"
                )
        return self


class CatalogEntry(NexoModel):
    catalog_id: str = Field(max_length=200)
    version: SemanticVersion
    audience: str = Field(max_length=40)
    path: str = Field(max_length=300)


class CatalogsConfig(NexoModel):
    """`config/catalogs.yaml`: catálogos A2UI negociables."""

    version: ConfigVersion
    catalogs: Annotated[list[CatalogEntry], Field(min_length=1, max_length=20)]


class RetryPolicy(NexoModel):
    """Política de reintento por operación (`DIE-F0-035`)."""

    max_attempts: int = Field(default=1, ge=1, le=5)
    retry_on: Annotated[list[ErrorCode], Field(max_length=10)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _never_retry_unknown_outcomes(self) -> Self:
        if ErrorCode.UNKNOWN_OUTCOME in self.retry_on:
            raise ValueError(
                "UNKNOWN_OUTCOME no puede estar en retry_on: reintentar una operación cuyo "
                "efecto se desconoce es exactamente cómo se duplica una escritura"
            )
        return self


class OperationPolicy(NexoModel):
    """Timeout y reintentos de una operación con nombre."""

    operation: Slug
    mode: ToolMode = ToolMode.READ
    timeout_ms: PositiveMillis = 5000
    retry: RetryPolicy = Field(default_factory=RetryPolicy)

    @model_validator(mode="after")
    def _writes_are_never_retried_automatically(self) -> Self:
        if self.mode is ToolMode.WRITE and self.retry.max_attempts != 1:
            raise ValueError(
                f"la operación de escritura {self.operation!r} declara "
                f"max_attempts={self.retry.max_attempts}; una escritura no se reintenta "
                f"automáticamente"
            )
        return self


class RunOutcomePolicy(NexoModel):
    """Qué detiene el run, qué produce `partial` y qué admite fallback (`DIE-F0-010`).

    Codificarlo aquí, y no solo en prosa, permite que el grafo consulte la regla
    en vez de que cada nodo improvise su propia interpretación.
    """

    halt_on: Annotated[list[ErrorCode], Field(max_length=20)] = Field(
        default_factory=lambda: [
            ErrorCode.CONFIGURATION_INVALID,
            ErrorCode.AUTHENTICATION_REQUIRED,
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.CONTRACT_INVALID,
        ]
    )
    partial_on: Annotated[list[ErrorCode], Field(max_length=20)] = Field(
        default_factory=lambda: [
            ErrorCode.UNKNOWN_OUTCOME,
            ErrorCode.RUN_TIMEOUT,
            ErrorCode.BUDGET_EXCEEDED,
        ]
    )
    fallback_on: Annotated[list[ErrorCode], Field(max_length=20)] = Field(
        default_factory=lambda: [
            ErrorCode.MODEL_UNAVAILABLE,
            ErrorCode.MODEL_OUTPUT_INVALID,
            ErrorCode.RATE_LIMITED,
            ErrorCode.PROVIDER_ERROR,
        ]
    )

    @model_validator(mode="after")
    def _categories_are_disjoint(self) -> Self:
        """Un mismo código no puede detener, degradar y permitir fallback a la vez."""
        halt, partial, fallback = set(self.halt_on), set(self.partial_on), set(self.fallback_on)
        for left_name, left, right_name, right in (
            ("halt_on", halt, "partial_on", partial),
            ("halt_on", halt, "fallback_on", fallback),
            ("partial_on", partial, "fallback_on", fallback),
        ):
            overlap = sorted(code.value for code in left & right)
            if overlap:
                raise ValueError(
                    f"los códigos {overlap} aparecen en {left_name} y en {right_name}; "
                    f"la reacción a un error debe ser inequívoca"
                )
        return self

    def is_halting(self, code: ErrorCode) -> bool:
        return code in self.halt_on

    def is_partial(self, code: ErrorCode) -> bool:
        return code in self.partial_on

    def allows_fallback(self, code: ErrorCode) -> bool:
        return code in self.fallback_on


class PoliciesConfig(NexoModel):
    """`config/policies.yaml`: presupuestos, timeouts, reintentos y desenlaces."""

    version: ConfigVersion
    run_budgets: Budgets = Field(default_factory=Budgets)
    agent_budgets: dict[AgentName, Budgets] = Field(default_factory=dict)
    operations: Annotated[list[OperationPolicy], Field(max_length=100)] = Field(
        default_factory=list
    )
    outcomes: RunOutcomePolicy = Field(default_factory=RunOutcomePolicy)

    @model_validator(mode="after")
    def _agent_budgets_fit_within_the_run(self) -> Self:
        """Ningún agente puede tener más presupuesto que el run completo."""
        for agent, budget in self.agent_budgets.items():
            if budget.deadline_ms > self.run_budgets.deadline_ms:
                raise ValueError(
                    f"el deadline del agente {agent.value!r} ({budget.deadline_ms} ms) supera "
                    f"el del run ({self.run_budgets.deadline_ms} ms)"
                )
            if budget.max_cost_usd > self.run_budgets.max_cost_usd:
                raise ValueError(
                    f"el presupuesto del agente {agent.value!r} ({budget.max_cost_usd} USD) "
                    f"supera el del run ({self.run_budgets.max_cost_usd} USD)"
                )
        return self


class NexoConfig(NexoModel):
    """Configuración completa validada al arranque (`DIE-F0-036`)."""

    model_router: ModelRouterConfig
    tool_registry: ToolRegistryConfig
    permissions: PermissionsConfig
    catalogs: CatalogsConfig
    policies: PoliciesConfig

    @property
    def policy_version(self) -> str:
        """Versión que se propaga a eventos y evaluaciones (`DIE-F0-037`)."""
        return self.policies.version

    @model_validator(mode="after")
    def _permission_rules_reference_registered_tools(self) -> Self:
        registered = {entry.name for entry in self.tool_registry.tools}
        dangling = sorted(
            {
                rule.tool
                for rule in self.permissions.rules
                if rule.tool is not None and rule.tool not in registered
            }
        )
        if dangling:
            raise ValueError(
                f"hay permisos que referencian tools no registradas: {dangling}; una tool sin "
                f"versión registrada se niega por defecto"
            )
        return self
