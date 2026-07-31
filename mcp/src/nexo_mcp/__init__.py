"""Publicación y ejecución de capacidades institucionales de Nexo IA.

En Fase 0 el paquete publica únicamente sus **puertos** y los dobles en memoria.
El server MCP, el registry versionado, las tools mock de dominio y el Mapper son
trabajo de Fase 1 (F1.8, F1.9) y Fase 3 (F3.2).
"""

from .ports import ToolAuthorizationError, ToolExecutorPort, ToolRegistryPort

__all__ = ["ToolAuthorizationError", "ToolExecutorPort", "ToolRegistryPort"]
