"""Orquestación de Nexo IA: estado, grafo, puertos y eventos.

Convierte un `RunRequest` en una ejecución observable, reanudable e idempotente.
No renderiza UI, no contiene SQL y no importa SDKs de canal ni de proveedor.
"""

from .configuration import load_config
from .events import EventEmitter
from .graph import MinimalGraph
from .reducers import merge_run_state

__all__ = ["EventEmitter", "MinimalGraph", "load_config", "merge_run_state"]
