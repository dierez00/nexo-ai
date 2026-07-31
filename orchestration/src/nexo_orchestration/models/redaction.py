"""Redacción de prompts y mensajes antes de registrarlos (`DIE-F1-008`).

Un log es un destino de datos como cualquier otro: si un prompt con el teléfono
de una persona acaba en un archivo, la política de PII se incumplió igual que si
hubiera acabado en un evento.

La regla es más simple que enmascarar bien: **el texto del prompt no se
registra**. De una invocación se guarda su forma —purpose, alias, versión de
prompt, tamaño— que es lo que sirve para depurar, y nunca su contenido. El
enmascarado de `redact_text` existe solo para los mensajes de error de
proveedor, que sí hay que leer y no controlamos.

Es una barrera sintáctica, igual que `reject_unsafe_keys`: reconoce las formas
frecuentes, no garantiza ausencia de PII (ver TD-03).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from nexo_contracts import Slug

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from ..ports.model import ChatRequest

MASK = "[redactado]"

# Formas frecuentes en español-MX. El orden importa: los patrones más
# específicos (CURP, RFC) van antes que los genéricos de dígitos.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("curp", re.compile(r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b")),
    ("rfc", re.compile(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b")),
    ("bearer", re.compile(r"(?i)\b(bearer|api[_-]?key|token)\s*[:=]?\s*[A-Za-z0-9._\-]{8,}")),
    ("phone", re.compile(r"\b\d{2,3}[\s-]?\d{3,4}[\s-]?\d{4}\b")),
    ("long_digits", re.compile(r"\b\d{9,}\b")),
)


def redact_text(text: str, *, max_length: int = 500) -> str:
    """Enmascara las formas reconocibles de PII y credenciales, y trunca."""
    redacted = text
    for _, pattern in _PATTERNS:
        redacted = pattern.sub(MASK, redacted)
    if len(redacted) > max_length:
        redacted = redacted[: max_length - 1] + "…"
    return redacted


def detected_signals(text: str) -> list[str]:
    """Nombres de las formas sensibles presentes en el texto, sin el texto."""
    return sorted({name for name, pattern in _PATTERNS if pattern.search(text)})


def describe_request(request: ChatRequest) -> dict[str, str | int | bool]:
    """Descripción registrable de una invocación: su forma, nunca su contenido.

    Deliberadamente **no** incluye `prompt` ni `variables`. Incluir el prompt
    "solo en depuración" es cómo un prompt con PII termina en producción.
    """
    signals = detected_signals(request.prompt)
    return {
        "purpose": request.purpose,
        "task_kind": request.task_kind.value,
        "requested_alias": request.alias,
        "output_contract": request.output_contract,
        "prompt_version": request.prompt_version,
        "prompt_chars": len(request.prompt),
        "variable_count": len(request.variables),
        "attempt": request.attempt,
        # Señal útil para auditar qué llega al modelo, sin transportar el dato.
        "sensitive_signals": ",".join(signals),
        "prompt_redacted": True,
    }


def purpose_of(request: ChatRequest) -> Slug:
    """Clave estable del punto de invocación; es segura para logs y métricas."""
    return request.purpose
