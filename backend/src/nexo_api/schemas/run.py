"""DTOs HTTP propios de runs.

Los contratos de ejecución, eventos e identidad viven exclusivamente en
``nexo_contracts``. Esta capa solo conserva la aceptación asíncrona de la API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from nexo_contracts import RunStatus


class RunAccepted(BaseModel):
    """Acuse inmediato de un run que se ejecuta en segundo plano."""

    run_id: str
    trace_id: str
    status: RunStatus
    events_url: str
    created_at: datetime
