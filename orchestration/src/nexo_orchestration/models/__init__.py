"""Gateway de modelos de Nexo IA (F1.1).

Vive en `orchestration` porque es aquí donde se declara `ChatModelPort` y donde
se carga la configuración. Los adapters de proveedor concretos son trabajo de
`integrations/models` (Dani): implementan `ChatAdapterPort` y no saben nada de
aliases, presupuesto ni fallback.
"""

from .adapters import AdapterResult, ChatAdapterPort, EmbeddingsAdapterPort
from .budget import BudgetExceededError, BudgetLedger
from .gateway import EmbeddingsGateway, ModelCallContext, ModelGateway, ModelOutcome
from .redaction import describe_request, detected_signals, redact_text

__all__ = [
    "AdapterResult",
    "BudgetExceededError",
    "BudgetLedger",
    "ChatAdapterPort",
    "EmbeddingsAdapterPort",
    "EmbeddingsGateway",
    "ModelCallContext",
    "ModelGateway",
    "ModelOutcome",
    "describe_request",
    "detected_signals",
    "redact_text",
]
