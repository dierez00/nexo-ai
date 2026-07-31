"""Gateway de modelos: aliases, validación, fallback y contabilidad (F1.1).

Es la única puerta por la que un agente habla con un modelo. Un agente pide un
**alias** (`structured_small`, `high_accuracy`, `offline_fake`) y declara qué
contrato debe cumplir la salida; nunca conoce el proveedor, el SDK ni el nombre
comercial del modelo (ADR 0003).

Cuatro responsabilidades, todas en un solo sitio a propósito:

1. **Resolver el alias** contra `config/model_router.yaml` (`DIE-F1-002`).
2. **Validar la salida** contra el contrato solicitado antes de devolverla
   (`DIE-F1-003`). Una salida que no cumple el schema es un fallo del modelo, no
   un dato del que el agente deba defenderse.
3. **Aplicar fallback** por indisponibilidad, timeout o salida inválida
   (`DIE-F1-005`), consultando la política de desenlaces en vez de improvisar.
4. **Registrar todo**: alias pedido y usado, tokens, costo, duración, intento y
   error (`DIE-F1-004`), sin que el prompt aparezca en ningún log
   (`DIE-F1-008`).

El perfil offline no es un modo degradado sino el último candidato de toda
cadena de fallback: mientras los aliases de proveedor estén deshabilitados —que
es el estado por defecto de la configuración— cada invocación acaba resolviendo
al modelo falso, y la demo completa corre sin red ni credenciales
(`DIE-F1-007`).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated

from pydantic import Field, JsonValue, ValidationError

from nexo_contracts import (
    ConfigurationError,
    ErrorCode,
    ModelAlias,
    ModelCandidate,
    ModelDecision,
    ModelDecisionReason,
    ModelInvocation,
    ModelPolicy,
    ModelTaskKind,
    NexoModel,
    NormalizedError,
    Outcome,
)
from nexo_contracts.config import (
    ModelAliasConfig,
    ModelRouterConfig,
    RetryPolicy,
    RunOutcomePolicy,
)
from nexo_contracts.ids import RunId, TraceId

from ..ports.clock import Clock, IdFactory
from ..ports.model import ChatRequest, ChatResponse, ModelPortError
from .adapters import ChatAdapterPort, EmbeddingsAdapterPort
from .budget import BudgetExceededError, BudgetLedger
from .redaction import describe_request

# Motivo con el que se registra un cambio de alias según qué falló. Se declara
# como tabla para que añadir un código de error obligue a decidir su motivo, en
# vez de caer en un `else` genérico que haría ilegible la traza.
_REASON_BY_ERROR: dict[ErrorCode, ModelDecisionReason] = {
    ErrorCode.MODEL_OUTPUT_INVALID: ModelDecisionReason.INVALID_OUTPUT_ESCALATION,
    ErrorCode.MODEL_UNAVAILABLE: ModelDecisionReason.PRIMARY_PROVIDER_DOWN,
    ErrorCode.PROVIDER_ERROR: ModelDecisionReason.PRIMARY_PROVIDER_DEGRADED,
    ErrorCode.RATE_LIMITED: ModelDecisionReason.PRIMARY_PROVIDER_DEGRADED,
}


@dataclass(frozen=True)
class ModelCallContext:
    """Atribución de una invocación a un run concreto.

    Sin ella no se puede construir un `ModelInvocation`, y sin `ModelInvocation`
    el run no registra costo ni tokens —que es un requisito del gate de
    rendimiento, no un extra de observabilidad.
    """

    run_id: RunId
    trace_id: TraceId
    ledger: BudgetLedger


class ModelOutcome[M: NexoModel](NexoModel):
    """Resultado completo de pedirle algo al gateway.

    Devuelve las tres cosas que el nodo necesita: el valor ya validado, la
    respuesta cruda y **todas** las invocaciones realizadas —incluidos los
    intentos fallidos, que también costaron dinero y deben aparecer en la traza.
    """

    value: M | None = None
    response: ChatResponse
    invocations: Annotated[list[ModelInvocation], Field(max_length=10)] = Field(
        default_factory=list
    )

    @property
    def total_cost_usd(self) -> float:
        return sum(invocation.estimated_cost_usd for invocation in self.invocations)

    @property
    def fell_back(self) -> bool:
        return self.response.decision.selected_alias != self.response.decision.requested_alias


@dataclass
class ModelGateway:
    """Implementación de `ChatModelPort` con routing por alias y fallback.

    Sustituible por cualquier otro `ChatModelPort`: el grafo y los agentes no
    saben si detrás hay un proveedor, un adapter mock o una grabación.
    """

    router: ModelRouterConfig
    outcomes: RunOutcomePolicy
    adapters: Mapping[str, ChatAdapterPort]
    clock: Clock
    ids: IdFactory
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    sleep: Callable[[float], Awaitable[None]] = field(default=asyncio.sleep, repr=False)
    max_alias_hops: int = field(
        default=3,
        metadata={"why": "cota dura: un fallback que encadena sin límite es un run colgado"},
    )
    max_total_attempts: int = field(
        default=5,
        metadata={"why": "ModelInvocation limita attempt a cinco y la traza debe ser acotada"},
    )

    def __post_init__(self) -> None:
        self._aliases: dict[str, ModelAliasConfig] = {
            entry.alias: entry for entry in self.router.aliases
        }
        self._policies: dict[ModelTaskKind, ModelPolicy] = {
            policy.task_kind: policy for policy in self.router.policies
        }
        missing = sorted(
            {
                entry.provider_ref.provider
                for entry in self.router.aliases
                if entry.enabled and entry.provider_ref.provider not in self.adapters
            }
        )
        if missing:
            raise ConfigurationError(
                "config/model_router.yaml",
                "aliases[].provider_ref.provider",
                f"proveedores habilitados sin adapter registrado: {missing}; un alias "
                f"habilitado que no se puede invocar es una configuración inválida",
            )

    # -- resolución de aliases --------------------------------------------

    def _alias_config(self, alias: ModelAlias) -> ModelAliasConfig:
        try:
            return self._aliases[alias]
        except KeyError:
            raise ConfigurationError(
                "config/model_router.yaml",
                "aliases",
                f"alias no registrado: {alias!r}; los aliases disponibles son "
                f"{sorted(self._aliases)}",
            ) from None

    def _is_invocable(self, alias: ModelAlias) -> bool:
        entry = self._aliases.get(alias)
        return entry is not None and entry.enabled and entry.provider_ref.provider in self.adapters

    def _policy(self, task_kind: ModelTaskKind) -> ModelPolicy | None:
        return self._policies.get(task_kind)

    def _entry_alias(self, request: ChatRequest) -> tuple[ModelAlias, ModelDecisionReason]:
        """Primer alias a intentar, y por qué.

        Si el alias pedido no es invocable —deshabilitado o sin adapter— la
        decisión se registra como `offline_profile` en vez de `policy_default`:
        el contrato de `ModelDecision` prohíbe cambiar de alias sin motivo
        explícito, precisamente para que un fallback silencioso sea imposible.
        """
        self._alias_config(request.alias)
        if self._is_invocable(request.alias):
            return request.alias, ModelDecisionReason.POLICY_DEFAULT

        policy = self._policy(request.task_kind)
        if policy is not None and self._is_invocable(policy.default_alias):
            return policy.default_alias, ModelDecisionReason.PRIMARY_PROVIDER_DOWN
        return self.router.offline_alias, ModelDecisionReason.OFFLINE_PROFILE

    def _next_alias(
        self,
        *,
        code: ErrorCode,
        policy: ModelPolicy | None,
        tried: Sequence[ModelAlias],
    ) -> tuple[ModelAlias, ModelDecisionReason] | None:
        """Siguiente candidato tras un fallo, o `None` si no hay fallback posible.

        La política de desenlaces manda: un error que no está en `fallback_on`
        —un permiso denegado, una configuración inválida— no se reintenta con
        otro modelo, porque cambiar de proveedor no arregla un problema de
        autorización.
        """
        if not self.outcomes.allows_fallback(code):
            return None

        candidates: list[tuple[ModelAlias, ModelDecisionReason]] = []
        if policy is not None:
            if code is ErrorCode.MODEL_OUTPUT_INVALID and policy.escalation_alias:
                candidates.append(
                    (policy.escalation_alias, ModelDecisionReason.INVALID_OUTPUT_ESCALATION)
                )
            if policy.fallback_alias:
                candidates.append((policy.fallback_alias, _REASON_BY_ERROR[code]))
        candidates.append((self.router.offline_alias, ModelDecisionReason.OFFLINE_PROFILE))

        for alias, reason in candidates:
            if alias not in tried and self._is_invocable(alias):
                return alias, reason
        return None

    def _considered(
        self, *, request: ChatRequest, policy: ModelPolicy | None
    ) -> list[ModelCandidate]:
        """Alternativas evaluadas, con el motivo de descarte de cada una.

        Es lo que hace explicable una decisión sin revelar secretos: el evento
        muestra qué se consideró y por qué se descartó, nunca la credencial ni
        el nombre comercial del modelo.
        """
        names: list[ModelAlias] = [request.alias]
        if policy is not None:
            for alias in (policy.default_alias, policy.escalation_alias, policy.fallback_alias):
                if alias is not None:
                    names.append(alias)
        names.append(self.router.offline_alias)

        candidates: list[ModelCandidate] = []
        for alias in dict.fromkeys(names):
            entry = self._aliases.get(alias)
            if entry is None:
                continue
            rejected: str | None = None
            if not entry.enabled:
                rejected = "alias_disabled"
            elif entry.provider_ref.provider not in self.adapters:
                rejected = "adapter_not_registered"
            candidates.append(
                ModelCandidate(
                    alias=alias,
                    capabilities=entry.capabilities,
                    score=0.0 if rejected else 1.0,
                    rejected_reason=rejected,
                )
            )
        return candidates

    # -- contabilidad ------------------------------------------------------

    @staticmethod
    def _cost(entry: ModelAliasConfig, *, input_tokens: int, output_tokens: int) -> float:
        """Costo derivado de la configuración, nunca de lo que reporte el adapter."""
        caps = entry.capabilities
        return (
            input_tokens / 1000 * caps.cost_per_1k_input_usd
            + output_tokens / 1000 * caps.cost_per_1k_output_usd
        )

    def _decision(
        self,
        *,
        request: ChatRequest,
        selected: ModelAlias,
        reason: ModelDecisionReason,
        considered: list[ModelCandidate],
    ) -> ModelDecision:
        return ModelDecision(
            requested_alias=request.alias,
            selected_alias=selected,
            reason=reason,
            considered=considered,
            policy_version=self.router.version,
            max_cost_usd=request.max_cost_usd,
        )

    def _record(
        self,
        *,
        context: ModelCallContext,
        decision: ModelDecision,
        attempt: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
        started_at: datetime,
        error: NormalizedError | None,
    ) -> ModelInvocation:
        return ModelInvocation(
            invocation_id=self.ids.new_id("mdl"),
            run_id=context.run_id,
            trace_id=context.trace_id,
            decision=decision,
            attempt=attempt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost_usd,
            duration_ms=duration_ms,
            schema_valid=error is None or error.code is not ErrorCode.MODEL_OUTPUT_INVALID,
            started_at=started_at,
            error=error,
        )

    # -- invocación --------------------------------------------------------

    async def invoke[M: NexoModel](
        self,
        request: ChatRequest,
        context: ModelCallContext,
        contract: type[M] | None = None,
    ) -> ModelOutcome[M]:
        """Invoca el modelo, valida la salida y aplica fallback si hace falta.

        Lanza `ModelPortError` cuando se agotan los candidatos: quien llama
        decide si eso degrada el run a `partial`, lo detiene o usa una plantilla
        determinista, consultando la misma política de desenlaces.
        """
        policy = self._policy(request.task_kind)
        considered = self._considered(request=request, policy=policy)
        alias, reason = self._entry_alias(request)

        invocations: list[ModelInvocation] = []
        tried: list[ModelAlias] = []
        last_error: NormalizedError | None = None
        call_started_ms = self.clock.monotonic_ms()
        attempt = 0
        alias_hops = 0

        while alias_hops < self.max_alias_hops and attempt < self.max_total_attempts:
            alias_hops += 1
            if alias not in tried:
                tried.append(alias)
            entry = self._alias_config(alias)
            decision = self._decision(
                request=request, selected=alias, reason=reason, considered=considered
            )
            alias_attempt = 0
            move_to_next_alias = False

            while alias_attempt < self.retry.max_attempts and attempt < self.max_total_attempts:
                alias_attempt += 1
                attempt += 1
                elapsed_call_ms = self.clock.monotonic_ms() - call_started_ms
                remaining_ms = request.deadline_ms - elapsed_call_ms
                if remaining_ms <= 0:
                    timeout_error = NormalizedError.from_code(
                        ErrorCode.RUN_TIMEOUT,
                        f"se agotó el deadline del purpose {request.purpose!r}",
                    )
                    invocations.append(
                        self._record(
                            context=context,
                            decision=decision,
                            attempt=attempt,
                            input_tokens=0,
                            output_tokens=0,
                            cost_usd=0.0,
                            duration_ms=0,
                            started_at=self.clock.now(),
                            error=timeout_error,
                        )
                    )
                    raise ModelPortError(timeout_error, invocations=tuple(invocations))

                # `DIE-F1-006`: el presupuesto se comprueba antes de gastar, no después.
                try:
                    context.ledger.ensure_affordable(
                        max_cost_usd=request.max_cost_usd, deadline_ms=remaining_ms
                    )
                except BudgetExceededError as exc:
                    invocations.append(
                        self._record(
                            context=context,
                            decision=decision,
                            attempt=attempt,
                            input_tokens=0,
                            output_tokens=0,
                            cost_usd=0.0,
                            duration_ms=0,
                            started_at=self.clock.now(),
                            error=exc.error,
                        )
                    )
                    raise ModelPortError(exc.error, invocations=tuple(invocations)) from exc

                started_at = self.clock.now()
                started_ms = self.clock.monotonic_ms()
                adapter = self.adapters[entry.provider_ref.provider]

                try:
                    result = await adapter.generate(
                        request,
                        model=entry.provider_ref.model,
                        output_contract=contract,
                        max_output_tokens=entry.capabilities.max_output_tokens,
                        timeout_ms=remaining_ms,
                    )
                except ModelPortError as exc:
                    elapsed = self.clock.monotonic_ms() - started_ms
                    duration_ms = exc.duration_ms or elapsed
                    cost = self._cost(
                        entry,
                        input_tokens=exc.input_tokens,
                        output_tokens=exc.output_tokens,
                    )
                    context.ledger.charge(
                        cost_usd=cost,
                        input_tokens=exc.input_tokens,
                        output_tokens=exc.output_tokens,
                    )
                    invocations.append(
                        self._record(
                            context=context,
                            decision=decision,
                            attempt=attempt,
                            input_tokens=exc.input_tokens,
                            output_tokens=exc.output_tokens,
                            cost_usd=cost,
                            duration_ms=duration_ms,
                            started_at=started_at,
                            error=exc.error,
                        )
                    )
                    last_error = exc.error
                    if await self._retry_current_alias(
                        error=exc.error,
                        alias_attempt=alias_attempt,
                        call_started_ms=call_started_ms,
                        deadline_ms=request.deadline_ms,
                    ):
                        continue
                    nxt = self._next_alias(code=exc.error.code, policy=policy, tried=tried)
                    if nxt is None:
                        raise ModelPortError(exc.error, invocations=tuple(invocations)) from exc
                    alias, reason = nxt
                    move_to_next_alias = True
                    break

                cost = self._cost(
                    entry, input_tokens=result.input_tokens, output_tokens=result.output_tokens
                )
                context.ledger.charge(
                    cost_usd=cost,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                )

                value: M | None = None
                schema_error: NormalizedError | None = None
                if contract is not None:
                    try:
                        value = contract.model_validate(result.data)
                    except ValidationError as exc:
                        schema_error = _output_contract_error(request.output_contract, exc)

                invocations.append(
                    self._record(
                        context=context,
                        decision=decision,
                        attempt=attempt,
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        cost_usd=cost,
                        duration_ms=result.duration_ms,
                        started_at=started_at,
                        error=schema_error,
                    )
                )

                if schema_error is None:
                    return ModelOutcome[M](
                        value=value,
                        response=ChatResponse(
                            data=result.data,
                            decision=decision,
                            input_tokens=result.input_tokens,
                            output_tokens=result.output_tokens,
                            estimated_cost_usd=cost,
                            duration_ms=result.duration_ms,
                        ),
                        invocations=invocations,
                    )

                last_error = schema_error
                if await self._retry_current_alias(
                    error=schema_error,
                    alias_attempt=alias_attempt,
                    call_started_ms=call_started_ms,
                    deadline_ms=request.deadline_ms,
                ):
                    continue
                nxt = self._next_alias(code=schema_error.code, policy=policy, tried=tried)
                if nxt is None:
                    raise ModelPortError(schema_error, invocations=tuple(invocations))
                alias, reason = nxt
                move_to_next_alias = True
                break

            if move_to_next_alias:
                continue
            break

        assert last_error is not None  # el bucle solo termina tras al menos un fallo
        exhausted = NormalizedError.from_code(
            last_error.code,
            f"se agotaron los intentos de modelo para el purpose "
            f"{request.purpose!r}; último motivo: {last_error.message}",
            outcome=last_error.outcome,
        )
        raise ModelPortError(
            exhausted,
            invocations=tuple(invocations),
        )

    async def _retry_current_alias(
        self,
        *,
        error: NormalizedError,
        alias_attempt: int,
        call_started_ms: int,
        deadline_ms: int,
    ) -> bool:
        """Espera, si cabe en el deadline, antes de repetir el mismo proveedor."""
        if error.code not in self.retry.retry_on or alias_attempt >= self.retry.max_attempts:
            return False
        remaining_ms = deadline_ms - (self.clock.monotonic_ms() - call_started_ms)
        delay_ms = error.retry_after_ms or 0
        if remaining_ms <= 0 or delay_ms >= remaining_ms:
            return False
        if delay_ms:
            await self.sleep(delay_ms / 1000)
        return True

    async def generate(self, request: ChatRequest) -> ChatResponse:
        """Conformidad con `ChatModelPort`, sin atribución a un run.

        Existe para que el gateway sea sustituible por cualquier otro
        `ChatModelPort` (y viceversa). No produce `ModelInvocation` porque no
        hay run al que atribuirla; los nodos del grafo usan `invoke`.
        """
        from nexo_contracts import Budgets

        context = ModelCallContext(
            run_id="run_unattributed",
            trace_id="trace_unattributed",
            ledger=BudgetLedger(budgets=Budgets()),
        )
        outcome: ModelOutcome[NexoModel] = await self.invoke(request, context)
        return outcome.response

    def describe(self, request: ChatRequest) -> dict[str, JsonValue]:
        """Descripción registrable de la invocación, con el prompt fuera."""
        return dict(describe_request(request))


def _output_contract_error(contract_name: str, exc: ValidationError) -> NormalizedError:
    """Traduce un fallo de validación a error normalizado, sin filtrar la salida.

    Se transporta la ruta del campo y el motivo, nunca el valor recibido: la
    salida de un modelo puede contener lo que sea, incluido lo que el usuario
    escribió.
    """
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first["loc"]) or "<raíz>"
    return NormalizedError.from_code(
        ErrorCode.MODEL_OUTPUT_INVALID,
        f"la salida no cumple el contrato {contract_name!r}: campo {location!r} — {first['msg']}",
        outcome=Outcome.KNOWN_FAILURE,
    )


@dataclass
class EmbeddingsGateway:
    """Segundo brazo de la interfaz única: vectorización por alias (`DIE-F1-001`).

    Satisface estructuralmente el `EmbeddingsPort` de `nexo_rag` sin importarlo:
    el puerto es un `Protocol` y declararlo aquí invertiría la dependencia entre
    módulos (mismo criterio que D-06 en `mcp`).

    Registra modelo y dimensión para que cada chunk indexado sepa con qué se
    vectorizó (`DIE-F1-017`); reindexar con otro modelo debe ser detectable.
    """

    router: ModelRouterConfig
    adapters: Mapping[str, EmbeddingsAdapterPort]
    alias: ModelAlias

    def __post_init__(self) -> None:
        entry = next((e for e in self.router.aliases if e.alias == self.alias), None)
        if entry is None:
            raise ConfigurationError(
                "config/model_router.yaml",
                "aliases",
                f"alias de embeddings no registrado: {self.alias!r}",
            )
        if entry.provider_ref.provider not in self.adapters:
            raise ConfigurationError(
                "config/model_router.yaml",
                "aliases[].provider_ref.provider",
                f"el alias de embeddings {self.alias!r} apunta al proveedor "
                f"{entry.provider_ref.provider!r}, que no tiene adapter registrado",
            )
        self._entry = entry
        self._adapter = self.adapters[entry.provider_ref.provider]

    @property
    def model_name(self) -> str:
        """Nombre completo `alias:modelo`, para registrarlo junto a cada chunk."""
        return f"{self.alias}:{self._entry.provider_ref.model}"

    @property
    def dimension(self) -> int:
        return self._adapter.dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._adapter.embed(texts, model=self._entry.provider_ref.model)
