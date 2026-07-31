"""Detección de prompt injection documental (`DIE-F1-025`, `DIE-F1-026`).

El contenido recuperado es **dato, nunca instrucción**. Un documento puede haber
sido alterado en origen, y la defensa no puede ser confiar en que no lo esté.

Dos decisiones deliberadas:

1. **Se detecta y se registra, no se descarta.** Borrar el fragmento ocultaría
   el ataque; entregarlo marcado permite que el verificador lo rechace, que el
   evento lo registre y que alguien lo investigue.
2. **La señal no cambia el plan.** Ni la allowlist de tools, ni los permisos, ni
   la ruta del run dependen de lo que diga un documento. Que este módulo exista
   no es lo que impide obedecer una injection: lo impide que ningún agente lea
   texto recuperado como instrucción.

Los patrones cubren español y las formas inglesas frecuentes. Es una barrera
sintáctica y se le escapará un ataque escrito con otras palabras; el corpus
adversarial de F2.9 (`DIE-F2-066`) debe ampliarla.
"""

from __future__ import annotations

import re

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "instruction_override",
        re.compile(
            r"(ignora|olvida|descarta)\s+(las?\s+|tus\s+|todas?\s+las?\s+)?"
            r"(instrucciones|reglas|indicaciones)"
            r"|ignore\s+(all\s+)?(previous|prior)\s+instructions",
            re.IGNORECASE,
        ),
    ),
    (
        "role_hijack",
        re.compile(
            r"(actua|actúa|comportate|compórtate)\s+como\s+(si\s+fueras|un|una)"
            r"|you\s+are\s+now\s+a"
            r"|asume\s+(el\s+)?(rol|papel)\s+de",
            re.IGNORECASE,
        ),
    ),
    (
        "tool_escalation",
        re.compile(
            r"(ejecuta|invoca|llama|usa)\s+(la\s+)?(tool|herramienta|funcion|función)"
            r"|sin\s+(pedir|solicitar)\s+confirmaci[oó]n"
            r"|permisos?\s+(ampliados|elevados|de\s+administrador)",
            re.IGNORECASE,
        ),
    ),
    (
        "exfiltration",
        re.compile(
            r"(revela|muestra|imprime|env[ií]a|comparte)\s+(el\s+|la\s+|tu\s+)?"
            r"(prompt|system\s+prompt|api[_\s-]?key|token|credencial|contrase[nñ]a)",
            re.IGNORECASE,
        ),
    ),
    (
        "authority_spoof",
        re.compile(
            r"(nota|mensaje|instrucci[oó]n)\s+(administrativa|del\s+sistema|para\s+el\s+asistente)"
            r"|este\s+documento\s+(te\s+)?autoriza",
            re.IGNORECASE,
        ),
    ),
)

PATTERN_NAMES: tuple[str, ...] = tuple(name for name, _ in _PATTERNS)


def detect_injection(text: str) -> list[str]:
    """Nombres de las señales de injection presentes en el texto, ordenados.

    Devuelve nombres estables —no fragmentos del texto— para que la señal pueda
    viajar en un evento sin transportar el propio ataque.
    """
    return sorted({name for name, pattern in _PATTERNS if pattern.search(text)})


def is_suspicious(text: str) -> bool:
    return bool(detect_injection(text))
