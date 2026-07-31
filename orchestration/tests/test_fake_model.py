"""El modelo falso reproduce éxito, salida inválida, timeout y fallback (§7.8)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nexo_contracts import ErrorCode, ModelTaskKind, Outcome
from nexo_orchestration.graph import FakeClassification
from nexo_orchestration.ports.model import ChatRequest, ModelPortError
from nexo_orchestration.testing import FakeBehavior, FakeChatModel, Scenario

pytestmark = pytest.mark.unit


def _request(purpose: str = "classify_request") -> ChatRequest:
    return ChatRequest(
        purpose=purpose,
        task_kind=ModelTaskKind.CLASSIFICATION,
        alias="offline_fake",
        output_contract="fake_classification",
        prompt="Quiero renovar mi licencia",
    )


async def test_success_returns_the_programmed_payload() -> None:
    model = FakeChatModel({"classify_request": Scenario(data={"domain": "vehiculos"})})
    response = await model.generate(_request())
    assert FakeClassification.model_validate(response.data).domain.value == "vehiculos"


async def test_invalid_output_fails_contract_validation() -> None:
    """La salida llega, pero no cumple el contrato: eso es un fallo del modelo."""
    model = FakeChatModel({"classify_request": Scenario(data={"domain": "inexistente"})})
    response = await model.generate(_request())
    with pytest.raises(ValidationError):
        FakeClassification.model_validate(response.data)


@pytest.mark.parametrize(
    ("behavior", "code"),
    [
        (FakeBehavior.TIMEOUT, ErrorCode.RUN_TIMEOUT),
        (FakeBehavior.RATE_LIMIT, ErrorCode.RATE_LIMITED),
        (FakeBehavior.PROVIDER_DOWN, ErrorCode.MODEL_UNAVAILABLE),
        (FakeBehavior.INVALID_OUTPUT, ErrorCode.MODEL_OUTPUT_INVALID),
    ],
)
async def test_failure_modes_produce_normalized_errors(behavior, code) -> None:
    model = FakeChatModel({"classify_request": Scenario(behavior=behavior)})
    with pytest.raises(ModelPortError) as caught:
        await model.generate(_request())
    assert caught.value.error.code is code


async def test_timeout_reports_an_unknown_outcome() -> None:
    """Un timeout no permite afirmar que la invocación no ocurrió."""
    model = FakeChatModel({"classify_request": Scenario(behavior=FakeBehavior.TIMEOUT)})
    with pytest.raises(ModelPortError) as caught:
        await model.generate(_request())
    assert caught.value.error.outcome is Outcome.UNKNOWN
    assert caught.value.error.retryable is False


async def test_script_advances_to_enable_fallback_testing() -> None:
    """Primer intento cae, segundo responde: es el patrón que ejercita el fallback."""
    model = FakeChatModel(
        {
            "classify_request": [
                Scenario(behavior=FakeBehavior.PROVIDER_DOWN),
                Scenario(data={"domain": "vehiculos"}),
            ]
        }
    )
    with pytest.raises(ModelPortError):
        await model.generate(_request())
    response = await model.generate(_request())
    assert response.data == {"domain": "vehiculos"}


async def test_last_scenario_repeats() -> None:
    """Un guion no tiene que anticipar cuántos reintentos hará el router."""
    model = FakeChatModel({"classify_request": [Scenario(data={"domain": "salud"})]})
    for _ in range(4):
        assert (await model.generate(_request())).data == {"domain": "salud"}


async def test_scenarios_are_keyed_by_purpose_not_by_prompt_text() -> None:
    """`DIE-F0-022`: reescribir el prompt no debe romper una prueba."""
    model = FakeChatModel({"classify_request": Scenario(data={"domain": "ganaderia"})})
    original = await model.generate(_request())
    rewritten = _request().model_copy(
        update={"prompt": "Necesito tramitar la renovación de mi licencia de conducir"}
    )
    assert (await model.generate(rewritten)).data == original.data


async def test_unprogrammed_purpose_fails_loudly() -> None:
    """Sin escenario ni default, el doble no inventa una respuesta."""
    model = FakeChatModel()
    with pytest.raises(KeyError, match="no tiene escenario"):
        await model.generate(_request("purpose_sin_programar"))


async def test_default_scenario_covers_unprogrammed_purposes() -> None:
    model = FakeChatModel(default=Scenario(data={"domain": "salud"}))
    assert (await model.generate(_request("otro"))).data == {"domain": "salud"}


async def test_calls_are_recorded_for_assertions() -> None:
    model = FakeChatModel({"classify_request": Scenario(data={"domain": "vehiculos"})})
    await model.generate(_request())
    await model.generate(_request())
    assert model.call_count("classify_request") == 2
    assert model.call_count() == 2
