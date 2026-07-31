"""Resolución central de contexto y precedencia (`DIE-F2-050`–`055`)."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from nexo_contracts import Deduction, FactOrigin, FactValue, NexoModel
from nexo_contracts.primitives import Slug, UtcDatetime


class ContextSource(StrEnum):
    SAFE_DEFAULT = "safe_default"
    CATALOG = "catalog"
    PROFILE = "profile"
    AUTHORIZED_HISTORY = "authorized_history"
    DOCUMENT = "document"
    AUTHORIZED_TOOL = "authorized_tool"
    CURRENT_MESSAGE = "current_message"
    CONFIRMATION = "confirmation"


_PRECEDENCE = {
    source: index
    for index, source in enumerate(
        (
            ContextSource.SAFE_DEFAULT,
            ContextSource.CATALOG,
            ContextSource.PROFILE,
            ContextSource.AUTHORIZED_HISTORY,
            ContextSource.DOCUMENT,
            ContextSource.AUTHORIZED_TOOL,
            ContextSource.CURRENT_MESSAGE,
            ContextSource.CONFIRMATION,
        )
    )
}


class ContextCandidate(NexoModel):
    key: Slug
    value: FactValue
    source: ContextSource
    observed_at: UtcDatetime
    explicit: bool = False
    write_eligible: bool = False


class ResolvedContextItem(NexoModel):
    key: Slug
    value: FactValue
    source: ContextSource
    observed_at: UtcDatetime
    deduction: Deduction | None = None
    superseded_sources: Annotated[list[ContextSource], Field(max_length=20)] = Field(
        default_factory=list
    )

    @property
    def may_feed_write(self) -> bool:
        return self.deduction is None or self.deduction.write_eligible


def resolve_context(candidates: list[ContextCandidate]) -> dict[str, ResolvedContextItem]:
    """Elige por precedencia y, dentro de una fuente, por observación más reciente."""
    grouped: dict[str, list[ContextCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.key, []).append(candidate)

    resolved: dict[str, ResolvedContextItem] = {}
    for key, values in grouped.items():
        selected = max(
            values,
            key=lambda item: (_PRECEDENCE[item.source], item.observed_at),
        )
        is_deduction = not selected.explicit
        deduction = (
            Deduction(
                value=selected.value,
                source=FactOrigin.DEDUCTION,
                confidence=1.0,
                confirmed_by_user=False,
                write_eligible=False,
                rationale=f"Contexto resuelto desde {selected.source.value}.",
            )
            if is_deduction
            else None
        )
        resolved[key] = ResolvedContextItem(
            key=key,
            value=selected.value,
            source=selected.source,
            observed_at=selected.observed_at,
            deduction=deduction,
            superseded_sources=sorted(
                {item.source for item in values if item is not selected},
                key=lambda source: _PRECEDENCE[source],
            ),
        )
    return resolved


__all__ = [
    "ContextCandidate",
    "ContextSource",
    "ResolvedContextItem",
    "resolve_context",
]
