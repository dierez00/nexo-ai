"""Acciones — confirmación con consentimiento e idempotencia."""

from __future__ import annotations

from nexo_api.services.actions.fake import FakeActionExecutor
from nexo_api.services.actions.port import ActionExecutor
from nexo_api.services.actions.real import RealActionExecutor, UnknownActionOutcome

__all__ = [
    "ActionExecutor",
    "FakeActionExecutor",
    "RealActionExecutor",
    "UnknownActionOutcome",
]
