"""Implementación backend del handoff de acciones desde orquestación."""

from __future__ import annotations

from nexo_api.repositories import pending_actions
from nexo_contracts import ActionRequest


class PostgresPendingActionSink:
    async def persist(self, action: ActionRequest, *, tenant_id: int) -> None:
        await pending_actions.create(tenant_id, action)
