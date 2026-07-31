"""Selección del backend de modelos sin abrir red ni cargar el corpus."""

from __future__ import annotations

import pytest
from nexo_api.services.orchestration import resolve_model_backend

from nexo_contracts import ConfigurationError

pytestmark = pytest.mark.unit


def test_auto_uses_gemini_only_when_the_key_exists() -> None:
    assert resolve_model_backend("auto", gemini_api_key="") == "offline"
    assert resolve_model_backend("auto", gemini_api_key="test-key") == "gemini"


def test_forced_offline_ignores_a_gemini_key() -> None:
    assert resolve_model_backend("offline", gemini_api_key="test-key") == "offline"


def test_forced_gemini_requires_a_key() -> None:
    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        resolve_model_backend("gemini", gemini_api_key="  ")
