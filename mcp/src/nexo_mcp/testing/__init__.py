"""Dobles de prueba de MCP (`DIE-F0-026`).

Sin red y sin sistemas institucionales. Reproducen éxito, timeout, error de
schema, permiso denegado y outcome desconocido, además de la idempotencia de las
escrituras.
"""

from .executor import ClockLike, InMemoryToolExecutor, ToolBehavior, ToolScenario
from .registry import InMemoryToolRegistry

__all__ = [
    "ClockLike",
    "InMemoryToolExecutor",
    "InMemoryToolRegistry",
    "ToolBehavior",
    "ToolScenario",
]
