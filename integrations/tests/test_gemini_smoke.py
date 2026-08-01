"""Smoke opt-in contra Gemini; nunca corre en la suite normal."""

from __future__ import annotations

import os

import pytest
from nexo_integrations.models import GeminiChatAdapter

from nexo_contracts import ModelTaskKind, NexoModel
from nexo_orchestration.ports.model import ChatRequest

# google-genai 2.13 crea una subclase interna de ClientSession. aiohttp avisa
# sobre esa herencia al abrir el cliente; no depende del adapter y no debe
# impedir que este smoke llegue al proveedor.
pytestmark = [
    pytest.mark.integration,
    pytest.mark.filterwarnings(
        "ignore:Inheritance class AiohttpClientSession from ClientSession is "
        "discouraged:DeprecationWarning"
    ),
]


class _SmokeAnswer(NexoModel):
    answer: str


@pytest.mark.skipif(
    os.environ.get("NEXO_RUN_GEMINI_SMOKE") != "1",
    reason="requiere NEXO_RUN_GEMINI_SMOKE=1 y una credencial real",
)
async def test_real_gemini_structured_output() -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("GEMINI_API_KEY no está configurada")

    adapter = GeminiChatAdapter(api_key=api_key)
    try:
        result = await adapter.generate(
            ChatRequest(
                purpose="gemini_smoke",
                task_kind=ModelTaskKind.DRAFTING,
                alias="structured_small",
                output_contract="gemini_smoke_answer",
                prompt="Responde con la palabra listo en el campo answer.",
                variables={},
                deadline_ms=20_000,
            ),
            model="gemini-3.5-flash-lite",
            output_contract=_SmokeAnswer,
            # Los modelos con razonamiento contabilizan sus thoughts dentro de
            # la salida; 128 puede agotarse antes de producir el JSON mínimo.
            max_output_tokens=1024,
            timeout_ms=20_000,
        )
    finally:
        await adapter.aclose()

    assert _SmokeAnswer.model_validate(result.data).answer
