"""`FakeActionExecutor` debe producir IDs opacos válidos en cada corrida.

Regresión: un `tool_call_id` construido con hex crudo (`uuid4().hex`) contiene
con frecuencia inaceptable una secuencia de 10+ dígitos decimales, que
`nexo_contracts.ids` rechaza como posible PII (teléfono/CURP). Eso hacía que
`FakeActionExecutor.execute` lanzara `ValidationError` de forma intermitente
y `confirm_action` lo reportara como `UNKNOWN_OUTCOME` (503) en vez de 200.
"""

from __future__ import annotations

import pytest
from nexo_api.services.actions.fake import FakeActionExecutor

from nexo_contracts import ActionRequest, ActionStatus

pytestmark = pytest.mark.asyncio

REQUEST = ActionRequest(
    action_id="act_5",
    run_id="run_42",
    tool_name="vehiculos.reservar_cita",
    input_schema_ref="contracts://vehiculos/reservar_cita.v1",
    tool_version="1.0.0",
    expected_version=1,
    parameters={"slot": "10:00"},
    required_permission="vehiculos.write",
)


async def test_the_fake_executor_never_produces_an_unopaque_tool_call_id() -> None:
    executor = FakeActionExecutor()
    for _ in range(500):
        result = await executor.execute(REQUEST)
        assert result.status is ActionStatus.SUCCEEDED
        assert result.tool_result is not None
        assert result.tool_result.confirmation is not None
