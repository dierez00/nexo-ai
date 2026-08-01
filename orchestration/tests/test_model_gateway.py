"""Gateway de modelos: aliases, validación, fallback, presupuesto y redacción (F1.1).

El router se construye aquí en código, no se lee de `config/`, por dos motivos:
la configuración del repositorio tiene todos los proveedores reales
deshabilitados —de modo que no habría cadena de fallback que ejercer— y una
prueba del gateway no debe romperse porque alguien cambie un YAML.
"""

from __future__ import annotations

import pytest

from nexo_contracts import (
    Budgets,
    ConfigurationError,
    Domain,
    ErrorCode,
    ModelDecisionReason,
    ModelTaskKind,
    NexoModel,
)
from nexo_contracts.config import (
    ModelAliasConfig,
    ModelCapabilities,
    ModelPolicy,
    ModelRouterConfig,
    ProviderRef,
    RetryPolicy,
    RunOutcomePolicy,
)
from nexo_orchestration.models import (
    BudgetLedger,
    EmbeddingsGateway,
    ModelCallContext,
    ModelGateway,
    describe_request,
    detected_signals,
    redact_text,
)
from nexo_orchestration.ports.model import ChatRequest, ModelPortError
from nexo_orchestration.testing import (
    FakeBehavior,
    FakeChatAdapter,
    FakeEmbeddingsAdapter,
    FrozenClock,
    Scenario,
    SequentialIdFactory,
)

pytestmark = pytest.mark.unit

PURPOSE = "classify_request"


class Classification(NexoModel):
    """Contrato de salida mínimo, solo para ejercer la validación."""

    domain: Domain


def _capabilities(*, cost_in: float = 0.0, cost_out: float = 0.0) -> ModelCapabilities:
    return ModelCapabilities(
        supports_structured_output=True,
        max_context_tokens=100_000,
        max_output_tokens=4096,
        cost_per_1k_input_usd=cost_in,
        cost_per_1k_output_usd=cost_out,
    )


def _router(
    *,
    primary_enabled: bool = True,
    escalation_enabled: bool = True,
) -> ModelRouterConfig:
    """Router con tres aliases: primario, escalada y perfil offline."""
    return ModelRouterConfig(
        version="router-test",
        allowed_providers=["fake", "vendor_a", "vendor_b"],
        aliases=[
            ModelAliasConfig(
                alias="offline_fake",
                provider_ref=ProviderRef(provider="fake", model="fake-deterministic-v1"),
                capabilities=_capabilities(),
                enabled=True,
            ),
            ModelAliasConfig(
                alias="structured_small",
                provider_ref=ProviderRef(provider="vendor_a", model="small-v1"),
                capabilities=_capabilities(cost_in=0.002, cost_out=0.006),
                enabled=primary_enabled,
            ),
            ModelAliasConfig(
                alias="high_accuracy",
                provider_ref=ProviderRef(provider="vendor_b", model="accurate-v1"),
                capabilities=_capabilities(cost_in=0.01, cost_out=0.04),
                enabled=escalation_enabled,
            ),
        ],
        offline_alias="offline_fake",
        policies=[
            ModelPolicy(
                task_kind=ModelTaskKind.CLASSIFICATION,
                default_alias="structured_small",
                escalation_alias="high_accuracy",
                fallback_alias="offline_fake",
                policy_version="router-test",
            )
        ],
    )


def _gateway(
    router: ModelRouterConfig,
    adapters: dict[str, FakeChatAdapter],
    *,
    outcomes: RunOutcomePolicy | None = None,
    retry: RetryPolicy | None = None,
    sleep: object | None = None,
    fill: bool = True,
) -> ModelGateway:
    """Gateway con adapters para todo alias habilitado.

    El gateway exige que cada alias habilitado tenga adapter, así que los que la
    prueba no programa se rellenan con un doble sin escenarios: si alguno se
    invocara, fallaría con un `KeyError` explícito en vez de pasar inadvertido.
    """
    resolved = dict(adapters)
    if fill:
        for entry in router.aliases:
            provider = entry.provider_ref.provider
            if entry.enabled and provider not in resolved:
                resolved[provider] = FakeChatAdapter(provider=provider)
    kwargs = {}
    if sleep is not None:
        kwargs["sleep"] = sleep
    return ModelGateway(
        router=router,
        outcomes=outcomes or RunOutcomePolicy(),
        adapters=resolved,
        clock=FrozenClock(),
        ids=SequentialIdFactory(),
        retry=retry or RetryPolicy(),
        **kwargs,  # type: ignore[arg-type]
    )


def _request(**overrides: object) -> ChatRequest:
    payload: dict[str, object] = {
        "purpose": PURPOSE,
        "task_kind": ModelTaskKind.CLASSIFICATION,
        "alias": "structured_small",
        "output_contract": "classification",
        "prompt": "Quiero renovar mi licencia",
        "variables": {},
    }
    payload.update(overrides)
    return ChatRequest(**payload)  # type: ignore[arg-type]


def _context(budgets: Budgets | None = None) -> ModelCallContext:
    return ModelCallContext(
        run_id="run_000001",
        trace_id="trace_000001",
        ledger=BudgetLedger(budgets=budgets or Budgets()),
    )


def _ok(**overrides: object) -> Scenario:
    return Scenario(data={"domain": "vehiculos"}, **overrides)  # type: ignore[arg-type]


# --- DIE-F1-002: resolución de alias ---------------------------------------


async def test_the_agent_never_learns_which_provider_served_the_request() -> None:
    """La respuesta habla de aliases; el proveedor y el modelo no aparecen."""
    gateway = _gateway(
        _router(), {"vendor_a": FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_a")}
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    decision = outcome.response.decision
    assert decision.selected_alias == "structured_small"
    serialized = decision.model_dump_json()
    assert "vendor_a" not in serialized
    assert "small-v1" not in serialized


async def test_an_unregistered_alias_is_a_configuration_error() -> None:
    gateway = _gateway(
        _router(), {"vendor_a": FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_a")}
    )

    with pytest.raises(ConfigurationError, match="alias no registrado"):
        await gateway.invoke(_request(alias="inventado"), _context(), Classification)


async def test_an_enabled_alias_without_adapter_fails_at_construction() -> None:
    """Un alias habilitado que nadie puede invocar es configuración inválida.

    Se detecta al construir el gateway y no en el tercer nodo del grafo, que es
    la misma regla de arranque que aplica `load_config` (`DIE-F0-036`).
    """
    with pytest.raises(ConfigurationError, match="sin adapter registrado"):
        _gateway(_router(), {"fake": FakeChatAdapter(provider="fake")}, fill=False)


# --- DIE-F1-007: perfil offline --------------------------------------------


async def test_a_disabled_primary_resolves_to_the_offline_profile() -> None:
    """Con los proveedores deshabilitados, todo acaba en el modelo falso."""
    gateway = _gateway(
        _router(primary_enabled=False, escalation_enabled=False),
        {"fake": FakeChatAdapter({PURPOSE: _ok()}, provider="fake")},
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    assert outcome.response.decision.selected_alias == "offline_fake"
    assert outcome.response.decision.reason is ModelDecisionReason.OFFLINE_PROFILE
    assert outcome.fell_back is True


async def test_the_offline_profile_is_reachable_without_credentials() -> None:
    """El alias offline no declara `api_key_ref`: la demo corre sin secretos."""
    router = _router()
    offline = next(entry for entry in router.aliases if entry.alias == router.offline_alias)
    assert offline.provider_ref.api_key_ref is None
    assert offline.enabled is True


# --- DIE-F1-003: validación de la salida -----------------------------------


async def test_output_that_breaks_the_contract_is_not_returned_to_the_agent() -> None:
    """Sin candidatos de respaldo, una salida inválida es un fallo del modelo."""
    router = _router(primary_enabled=False, escalation_enabled=False)
    gateway = _gateway(
        router,
        {"fake": FakeChatAdapter({PURPOSE: Scenario(data={"domain": "narnia"})}, provider="fake")},
    )

    with pytest.raises(ModelPortError) as excinfo:
        await gateway.invoke(_request(), _context(), Classification)

    assert excinfo.value.error.code is ErrorCode.MODEL_OUTPUT_INVALID


async def test_a_validation_failure_never_leaks_the_model_output() -> None:
    """El mensaje de error lleva campo y motivo, nunca el valor recibido."""
    router = _router(primary_enabled=False, escalation_enabled=False)
    gateway = _gateway(
        router,
        {
            "fake": FakeChatAdapter(
                {PURPOSE: Scenario(data={"domain": "secreto-del-usuario"})}, provider="fake"
            )
        },
    )

    with pytest.raises(ModelPortError) as excinfo:
        await gateway.invoke(_request(), _context(), Classification)

    assert "secreto-del-usuario" not in excinfo.value.error.message
    assert "domain" in excinfo.value.error.message


async def test_without_a_contract_the_gateway_does_not_invent_validation() -> None:
    """Pedir sin contrato devuelve los datos crudos y `value` vacío."""
    gateway = _gateway(
        _router(), {"vendor_a": FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_a")}
    )

    outcome = await gateway.invoke(_request(), _context())

    assert outcome.value is None
    assert outcome.response.data == {"domain": "vehiculos"}


# --- DIE-F1-005: fallback ---------------------------------------------------


async def test_invalid_output_escalates_before_falling_back() -> None:
    """Una salida inválida sube de precisión antes de rendirse (escalada)."""
    gateway = _gateway(
        _router(),
        {
            "vendor_a": FakeChatAdapter(
                {PURPOSE: Scenario(data={"domain": "narnia"})}, provider="vendor_a"
            ),
            "vendor_b": FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_b"),
            "fake": FakeChatAdapter({PURPOSE: _ok()}, provider="fake"),
        },
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    assert outcome.response.decision.selected_alias == "high_accuracy"
    assert outcome.response.decision.reason is ModelDecisionReason.INVALID_OUTPUT_ESCALATION
    assert outcome.value == Classification(domain=Domain.VEHICULOS)


@pytest.mark.parametrize(
    ("behavior", "expected_reason"),
    [
        (FakeBehavior.PROVIDER_DOWN, ModelDecisionReason.PRIMARY_PROVIDER_DOWN),
        (FakeBehavior.RATE_LIMIT, ModelDecisionReason.PRIMARY_PROVIDER_DEGRADED),
    ],
)
async def test_provider_failures_fall_back_with_an_explicit_reason(
    behavior: FakeBehavior, expected_reason: ModelDecisionReason
) -> None:
    """Todo cambio de alias declara su motivo; `policy_default` no vale."""
    gateway = _gateway(
        _router(escalation_enabled=False),
        {
            "vendor_a": FakeChatAdapter(
                {PURPOSE: Scenario(behavior=behavior)}, provider="vendor_a"
            ),
            "fake": FakeChatAdapter({PURPOSE: _ok()}, provider="fake"),
        },
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    assert outcome.response.decision.selected_alias == "offline_fake"
    assert outcome.response.decision.reason is expected_reason


async def test_a_timeout_is_not_a_fallback_condition() -> None:
    """`RUN_TIMEOUT` degrada el run; no se arregla cambiando de proveedor.

    La política de desenlaces lo clasifica en `partial_on`, no en `fallback_on`,
    y el gateway obedece esa clasificación en vez de tener su propia opinión.
    """
    gateway = _gateway(
        _router(escalation_enabled=False),
        {
            "vendor_a": FakeChatAdapter(
                {PURPOSE: Scenario(behavior=FakeBehavior.TIMEOUT)}, provider="vendor_a"
            ),
            "fake": FakeChatAdapter({PURPOSE: _ok()}, provider="fake"),
        },
    )

    with pytest.raises(ModelPortError) as excinfo:
        await gateway.invoke(_request(), _context(), Classification)

    assert excinfo.value.error.code is ErrorCode.RUN_TIMEOUT


async def test_a_non_fallbackable_error_stops_immediately() -> None:
    """Un código fuera de `fallback_on` no consume candidatos de respaldo."""
    outcomes = RunOutcomePolicy(fallback_on=[])
    fake = FakeChatAdapter({PURPOSE: _ok()}, provider="fake")
    gateway = _gateway(
        _router(escalation_enabled=False),
        {
            "vendor_a": FakeChatAdapter(
                {PURPOSE: Scenario(behavior=FakeBehavior.PROVIDER_DOWN)}, provider="vendor_a"
            ),
            "fake": fake,
        },
        outcomes=outcomes,
    )

    with pytest.raises(ModelPortError):
        await gateway.invoke(_request(), _context(), Classification)

    assert fake.call_count() == 0


async def test_transient_error_retries_same_alias_and_records_both_attempts() -> None:
    adapter = FakeChatAdapter(
        {
            PURPOSE: [
                Scenario(behavior=FakeBehavior.RATE_LIMIT),
                _ok(),
            ]
        },
        provider="vendor_a",
    )
    gateway = _gateway(
        _router(escalation_enabled=False),
        {"vendor_a": adapter},
        outcomes=RunOutcomePolicy(fallback_on=[]),
        retry=RetryPolicy(max_attempts=2, retry_on=[ErrorCode.RATE_LIMITED]),
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    assert adapter.call_count() == 2
    assert [item.attempt for item in outcome.invocations] == [1, 2]
    assert [item.decision.selected_alias for item in outcome.invocations] == [
        "structured_small",
        "structured_small",
    ]
    assert outcome.invocations[0].error is not None
    assert outcome.invocations[1].error is None


async def test_retry_after_is_honored_only_when_it_fits_in_deadline() -> None:
    delays: list[float] = []

    async def record_sleep(seconds: float) -> None:
        delays.append(seconds)

    adapter = FakeChatAdapter(
        {
            PURPOSE: [
                Scenario(behavior=FakeBehavior.RATE_LIMIT, retry_after_ms=50),
                _ok(),
            ]
        },
        provider="vendor_a",
    )
    gateway = _gateway(
        _router(escalation_enabled=False),
        {"vendor_a": adapter},
        outcomes=RunOutcomePolicy(fallback_on=[]),
        retry=RetryPolicy(max_attempts=2, retry_on=[ErrorCode.RATE_LIMITED]),
        sleep=record_sleep,
    )

    await gateway.invoke(_request(deadline_ms=100), _context(), Classification)

    assert delays == [0.05]

    no_time = FakeChatAdapter(
        {PURPOSE: Scenario(behavior=FakeBehavior.RATE_LIMIT, retry_after_ms=100)},
        provider="vendor_a",
    )
    gateway = _gateway(
        _router(escalation_enabled=False),
        {"vendor_a": no_time},
        outcomes=RunOutcomePolicy(fallback_on=[]),
        retry=RetryPolicy(max_attempts=2, retry_on=[ErrorCode.RATE_LIMITED]),
        sleep=record_sleep,
    )

    with pytest.raises(ModelPortError) as caught:
        await gateway.invoke(_request(deadline_ms=100), _context(), Classification)

    assert len(caught.value.invocations) == 1
    assert no_time.call_count() == 1


# --- DIE-F1-004: telemetría --------------------------------------------------


async def test_every_attempt_is_recorded_including_the_one_that_failed() -> None:
    """Un intento fallido costó dinero: ocultarlo haría mentir al presupuesto."""
    gateway = _gateway(
        _router(escalation_enabled=False),
        {
            "vendor_a": FakeChatAdapter(
                {PURPOSE: Scenario(behavior=FakeBehavior.PROVIDER_DOWN)}, provider="vendor_a"
            ),
            "fake": FakeChatAdapter({PURPOSE: _ok()}, provider="fake"),
        },
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    assert len(outcome.invocations) == 2
    failed, succeeded = outcome.invocations
    assert failed.decision.selected_alias == "structured_small"
    assert failed.error is not None
    assert failed.attempt == 1
    assert succeeded.decision.selected_alias == "offline_fake"
    assert succeeded.error is None
    assert succeeded.attempt == 2


async def test_cost_comes_from_configuration_not_from_the_adapter() -> None:
    """El precio de un modelo está escrito en un solo sitio: la configuración."""
    gateway = _gateway(
        _router(),
        {
            "vendor_a": FakeChatAdapter(
                # `cost_usd` del escenario es deliberadamente absurdo y se ignora.
                {PURPOSE: _ok(input_tokens=1000, output_tokens=500, cost_usd=99.0)},
                provider="vendor_a",
            )
        },
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    # 1000/1000 * 0.002 + 500/1000 * 0.006 = 0.005
    assert outcome.response.estimated_cost_usd == pytest.approx(0.005)
    assert outcome.total_cost_usd == pytest.approx(0.005)


async def test_invalid_output_is_recorded_as_schema_invalid() -> None:
    gateway = _gateway(
        _router(),
        {
            "vendor_a": FakeChatAdapter(
                {PURPOSE: Scenario(data={"domain": "narnia"})}, provider="vendor_a"
            ),
            "vendor_b": FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_b"),
        },
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    assert outcome.invocations[0].schema_valid is False
    assert outcome.invocations[-1].schema_valid is True


async def test_the_decision_explains_which_alternatives_were_discarded() -> None:
    gateway = _gateway(
        _router(primary_enabled=False, escalation_enabled=False),
        {"fake": FakeChatAdapter({PURPOSE: _ok()}, provider="fake")},
    )

    outcome = await gateway.invoke(_request(), _context(), Classification)

    reasons = {c.alias: c.rejected_reason for c in outcome.response.decision.considered}
    assert reasons["structured_small"] == "alias_disabled"
    assert reasons["high_accuracy"] == "alias_disabled"
    assert reasons["offline_fake"] is None


# --- DIE-F1-006: presupuesto y deadline --------------------------------------


async def test_an_exhausted_budget_stops_the_call_before_spending() -> None:
    adapter = FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_a")
    gateway = _gateway(_router(), {"vendor_a": adapter})
    context = _context(Budgets(max_cost_usd=0.001))

    with pytest.raises(ModelPortError) as excinfo:
        await gateway.invoke(_request(max_cost_usd=0.05), context, Classification)

    assert excinfo.value.error.code is ErrorCode.BUDGET_EXCEEDED
    assert adapter.call_count() == 0


async def test_a_call_longer_than_the_remaining_deadline_is_refused() -> None:
    adapter = FakeChatAdapter({PURPOSE: _ok()}, provider="vendor_a")
    gateway = _gateway(_router(), {"vendor_a": adapter})
    context = _context(Budgets(deadline_ms=20000))
    context.ledger.observe_elapsed(19_000)

    with pytest.raises(ModelPortError) as excinfo:
        await gateway.invoke(_request(deadline_ms=8000), context, Classification)

    assert excinfo.value.error.code is ErrorCode.RUN_TIMEOUT
    assert adapter.call_count() == 0


async def test_spending_accumulates_across_calls_in_the_same_run() -> None:
    adapter = FakeChatAdapter(
        {PURPOSE: _ok(input_tokens=1000, output_tokens=0)}, provider="vendor_a"
    )
    gateway = _gateway(_router(), {"vendor_a": adapter})
    context = _context()

    await gateway.invoke(_request(), context, Classification)
    await gateway.invoke(_request(), context, Classification)

    assert context.ledger.spent_usd == pytest.approx(0.004)
    assert context.ledger.spent_tokens == 2000
    assert context.ledger.invocations == 2


# --- DIE-F1-008: redacción ---------------------------------------------------


def test_the_prompt_never_appears_in_what_gets_logged() -> None:
    described = describe_request(_request(prompt="Mi CURP es GOMC800101HDFXXX09"))

    assert "prompt" not in {
        k for k in described if k not in {"prompt_chars", "prompt_version", "prompt_redacted"}
    }
    assert "GOMC800101HDFXXX09" not in str(described)
    assert described["prompt_chars"] == len("Mi CURP es GOMC800101HDFXXX09")
    assert described["sensitive_signals"] == "curp"


@pytest.mark.parametrize(
    ("text", "signal"),
    [
        ("escribe a diego@example.com", "email"),
        ("mi CURP es GOMC800101HDFXXX09", "curp"),
        ("Authorization: Bearer abc123def456", "bearer"),
        ("llámame al 618 123 4567", "phone"),
    ],
)
@pytest.mark.security
def test_recognisable_pii_and_credentials_are_masked(text: str, signal: str) -> None:
    redacted = redact_text(text)

    assert signal in detected_signals(text)
    assert "[redactado]" in redacted


@pytest.mark.security
def test_redaction_truncates_so_a_long_prompt_cannot_leak_by_volume() -> None:
    assert len(redact_text("a" * 5000, max_length=120)) == 120


# --- DIE-F1-001: embeddings detrás del mismo mecanismo -----------------------


async def test_embeddings_resolve_by_alias_and_record_model_and_dimension() -> None:
    gateway = EmbeddingsGateway(
        router=_router(),
        adapters={"fake": FakeEmbeddingsAdapter(provider="fake", dimension=64)},
        alias="offline_fake",
    )

    vectors = await gateway.embed(["renovación de licencia", "uso de suelo"])

    assert gateway.model_name == "offline_fake:fake-deterministic-v1"
    assert gateway.dimension == 64
    assert [len(vector) for vector in vectors] == [64, 64]


async def test_embeddings_are_deterministic_for_the_same_text() -> None:
    gateway = EmbeddingsGateway(
        router=_router(),
        adapters={"fake": FakeEmbeddingsAdapter(provider="fake")},
        alias="offline_fake",
    )

    first = await gateway.embed(["licencia"])
    second = await gateway.embed(["licencia"])

    assert first == second


def test_an_embeddings_alias_without_adapter_fails_at_construction() -> None:
    with pytest.raises(ConfigurationError, match="no tiene adapter registrado"):
        EmbeddingsGateway(
            router=_router(),
            adapters={"fake": FakeEmbeddingsAdapter(provider="fake")},
            alias="structured_small",
        )
