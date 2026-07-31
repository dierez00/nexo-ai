"""Puertos de ejecución de la orquestación (`DIE-F0-021`).

Un puerto es un `Protocol` sin implementación: describe lo que la orquestación
necesita, no cómo se obtiene. Los agentes y el grafo dependen únicamente de
estos protocolos, de modo que sustituir un doble de prueba por un adapter real
no cambia ningún caso de uso ni ningún contrato (`DIE-F0-030`).

Los puertos con I/O son asíncronos porque sus adapters reales lo serán (red,
base de datos, proveedores). `Clock` e `IdFactory` son síncronos: no hacen I/O y
existen solo para hacer reproducibles las ejecuciones (`DIE-F0-028`).
"""

from .checkpoints import CheckpointStorePort
from .clock import Clock, IdFactory
from .events import EventSinkPort
from .model import ChatModelPort, ChatRequest, ChatResponse

__all__ = [
    "ChatModelPort",
    "ChatRequest",
    "ChatResponse",
    "CheckpointStorePort",
    "Clock",
    "EventSinkPort",
    "IdFactory",
]
