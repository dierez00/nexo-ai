"""Lectura y escritura estable de streams JSONL A2UI v0.9.1 (`DIE-F1-109`)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from nexo_contracts import A2UIAction, A2UIMessage, A2UISurface, Channel


def render_jsonl(messages: Sequence[A2UIMessage] | A2UISurface) -> str:
    """Serializa una unidad de protocolo por línea, lista para el renderer."""
    stream = messages.messages if isinstance(messages, A2UISurface) else messages
    return "\n".join(message.model_dump_json_wire() for message in stream) + "\n"


def parse_jsonl(payload: str) -> tuple[A2UIMessage, ...]:
    """Valida un stream y conserva el número de línea en cualquier error."""
    messages: list[A2UIMessage] = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            messages.append(A2UIMessage.model_validate_json(line))
        except ValueError as exc:
            raise ValueError(f"JSONL A2UI inválido en línea {line_number}: {exc}") from exc
    if not messages:
        raise ValueError("el stream JSONL A2UI está vacío")
    return tuple(messages)


def load_jsonl(path: Path) -> tuple[A2UIMessage, ...]:
    """Carga un fixture UTF-8 y lo valida contra el contrato de mensajes."""
    return parse_jsonl(path.read_text(encoding="utf-8"))


def surface_from_messages(
    messages: Sequence[A2UIMessage],
    *,
    channel: Channel = Channel.WEB,
    actions: Sequence[A2UIAction] = (),
) -> A2UISurface:
    """Cierra un stream como superficie para ejecutar el validador de servidor."""
    first = messages[0] if messages else None
    if first is None or first.create_surface is None:
        raise ValueError("el stream debe iniciar con createSurface")
    return A2UISurface(
        surface_id=first.create_surface.surface_id,
        catalog_id=first.create_surface.catalog_id,
        channel=channel,
        messages=list(messages),
        actions=list(actions),
    )


__all__ = ["load_jsonl", "parse_jsonl", "render_jsonl", "surface_from_messages"]
