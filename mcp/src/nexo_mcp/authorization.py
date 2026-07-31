"""Autorización de invocaciones contra la matriz de permisos (`DIE-F1-066`).

La matriz vive en `config/permissions.yaml` y **deniega por defecto**: sin una
regla que conceda, no hay permiso. Aquí solo se evalúa.

Dos capas evalúan lo mismo y ninguna confía en la otra (ADR 0005): el registry
filtra la lista **antes** de mostrársela al modelo, y el executor revalida
**en el momento de ejecutar**. La segunda no es redundante: entre que el
supervisor filtró y el agente pidió, el agente pudo pedir cualquier cosa.

Los motivos de denegación son códigos estables y no explican de más
(`DIE-F2-015`): «no tienes permiso» es lo que la persona debe leer; qué regla
concreta faltó es información de auditoría, no de respuesta.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from nexo_contracts import ToolMetadata, ToolMode
from nexo_contracts.config import PermissionsConfig


class DenialReason(StrEnum):
    """Motivos estables de denegación, para auditoría y evaluación."""

    TOOL_NOT_REGISTERED = "tool_not_registered"
    TOOL_DISABLED = "tool_disabled"
    ROLE_NOT_ALLOWED = "role_not_allowed"
    INSTITUTION_MISMATCH = "institution_mismatch"
    NO_PERMISSION_RULE = "no_permission_rule"
    MODE_NOT_GRANTED = "mode_not_granted"
    CONFIRMATION_REQUIRED = "confirmation_required"
    IDEMPOTENCY_KEY_REQUIRED = "idempotency_key_required"
    VERSION_MISMATCH = "version_mismatch"


@dataclass(frozen=True)
class AuthorizationDecision:
    """Resultado de evaluar una invocación."""

    allowed: bool
    reason: DenialReason | None = None

    @classmethod
    def deny(cls, reason: DenialReason) -> AuthorizationDecision:
        return cls(allowed=False, reason=reason)

    @classmethod
    def allow(cls) -> AuthorizationDecision:
        return cls(allowed=True)


@dataclass
class PermissionMatrix:
    """Evaluador de `config/permissions.yaml`."""

    config: PermissionsConfig

    def __post_init__(self) -> None:
        if self.config.default_allow:  # pragma: no cover - el contrato ya lo impide
            raise ValueError("la matriz no puede conceder por defecto")

    def grants(
        self,
        *,
        institution_id: str,
        roles: list[str],
        tool: ToolMetadata,
        mode: ToolMode,
    ) -> AuthorizationDecision:
        """¿Alguna regla concede esta operación a alguno de estos roles?

        Una regla con `tool: null` cubre todas las tools del dominio, pero el
        contrato de `PermissionsConfig` impide que una regla así conceda
        `write`: una escritura se autoriza tool por tool.
        """
        actor_roles = set(roles)
        for rule in self.config.rules:
            if not rule.allow:
                continue
            if rule.institution_id != institution_id:
                continue
            if rule.role not in actor_roles:
                continue
            if rule.domain is not tool.domain:
                continue
            if rule.tool is not None and rule.tool != tool.name:
                continue
            if mode in rule.operations:
                return AuthorizationDecision.allow()
        return AuthorizationDecision.deny(DenialReason.NO_PERMISSION_RULE)

    def visible_modes(
        self, *, institution_id: str, roles: list[str], tool: ToolMetadata
    ) -> frozenset[ToolMode]:
        """Modos que este actor tiene concedidos sobre esta tool."""
        return frozenset(
            mode
            for mode in ToolMode
            if self.grants(institution_id=institution_id, roles=roles, tool=tool, mode=mode).allowed
        )
