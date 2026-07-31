"""Fallback de canal en texto plano (`DIE-F1-106`, `DIE-F1-107`).

Si la superficie no valida —o el canal no sabe renderizar A2UI— la persona
recibe texto equivalente, **nunca nada**. Una validación fallida es un problema
nuestro, y hacérselo pagar a quien preguntaba con una pantalla en blanco es la
peor forma de resolverlo.

El fallback se construye desde los mismos `VerifiedFacts` que la superficie, no
desde la superficie. Derivarlo del árbol de componentes significaría que un
árbol malformado produce un fallback malformado, justo cuando el fallback es lo
único que queda.

WhatsApp recibe lista numerada (`DIE-F1-107`): el canal no tiene viñetas fiables
ni encabezados, y una lista numerada sobrevive a cualquier cliente.
"""

from __future__ import annotations

from nexo_contracts import (
    ActionRequest,
    Channel,
    ChannelFallback,
    Estimate,
    FactCategory,
    VerifiedFacts,
)

from .builder import format_money

MAX_TEXT_CHARS = 4000


def build_fallback(
    facts: VerifiedFacts,
    *,
    channel: Channel,
    reason: str,
    estimate: Estimate | None = None,
    pending_action: ActionRequest | None = None,
    headline: str = "Esto es lo que encontré",
    warnings: tuple[str, ...] = (),
    is_mock: bool = True,
) -> ChannelFallback:
    """Construye la representación textual equivalente a la superficie."""
    accepted = list(facts.accepted())
    items: list[str] = []

    for fact in accepted:
        if fact.category is FactCategory.REQUIREMENT:
            items.append(f"Requisito: {fact.claim}")
    for fact in accepted:
        if fact.category is FactCategory.COST:
            money = fact.value.money
            suffix = f" — {format_money(money)}" if money is not None else ""
            items.append(f"Costo: {fact.claim}{suffix}")
    for fact in accepted:
        if fact.category not in {FactCategory.REQUIREMENT, FactCategory.COST}:
            items.append(fact.claim)

    lines: list[str] = [headline]
    if is_mock:
        # `DIE-F1-096`: la naturaleza mock se dice siempre, y en el fallback con
        # más razón: es el canal donde menos contexto visual hay.
        lines.append(
            "Aviso: esta respuesta usa datos de demostración y no sustituye al trámite real."
        )

    if channel is Channel.WHATSAPP:
        lines.extend(f"{index}. {item}" for index, item in enumerate(items, start=1))
    else:
        lines.extend(f"- {item}" for item in items)

    if estimate is not None and estimate.total_cost is not None:
        lines.append(f"Total estimado: {format_money(estimate.total_cost)}")

    sources = sorted(
        {
            citation.source_id
            for fact in facts.facts
            for citation in fact.citations
            if citation.is_active
        }
    )
    if sources:
        lines.append(f"Fuentes: {', '.join(sources)}")

    lines.extend(f"Aviso: {warning}" for warning in warnings)

    action_hint: str | None = None
    if pending_action is not None:
        action_hint = "Responde CONFIRMAR para continuar. La operación se enviará una sola vez."
        lines.append(action_hint)

    if not items:
        lines.append(
            "No encontré documentación vigente que respalde una respuesta, así que "
            "prefiero no afirmar nada."
        )

    text = "\n".join(lines)[:MAX_TEXT_CHARS]
    return ChannelFallback(
        channel=channel,
        reason=reason,
        text=text,
        numbered_items=items[:50] if channel is Channel.WHATSAPP else [],
        action_hint=action_hint,
    )
