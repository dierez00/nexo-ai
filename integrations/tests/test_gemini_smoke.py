"""Smoke opt-in contra Gemini; nunca corre en la suite normal."""

from __future__ import annotations

import os

import pytest
from nexo_integrations.models import GeminiChatAdapter

from nexo_contracts import ModelTaskKind, NexoModel
from nexo_orchestration.ports.model import ChatRequest

pytestmark = pytest.mark.integration


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
            model="gemini-3.6-flash",
            output_contract=_SmokeAnswer,
            max_output_tokens=128,
            timeout_ms=20_000,
        )
    finally:
        await adapter.aclose()

    assert _SmokeAnswer.model_validate(result.data).answer
