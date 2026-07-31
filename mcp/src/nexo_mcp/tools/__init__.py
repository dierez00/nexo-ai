"""Tools mock del MVP (F1.9).

Cada tool declara metadata versionada, contratos de entrada y salida, y su
adapter. El adapter mock conserva el wire shape del adapter real futuro
(`DIE-F1-072`).
"""

from .definitions import DEFINITIONS_BY_NAME, TOOL_DEFINITIONS, ToolDefinition

__all__ = ["DEFINITIONS_BY_NAME", "TOOL_DEFINITIONS", "ToolDefinition"]
