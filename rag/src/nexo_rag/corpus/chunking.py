"""Fragmentación estable por tipo documental (`DIE-F1-013`).

Dos propiedades mandan sobre cualquier otra consideración:

1. **Estabilidad.** El mismo archivo produce siempre los mismos fragmentos con
   los mismos offsets. Un chunking que varía entre corridas invalida las
   citaciones ya emitidas: `frag_...` dejaría de apuntar al mismo texto.
2. **Trazabilidad al original.** Cada fragmento guarda `char_start`, `char_end`
   y su encabezado, de modo que una citación puede reconstruirse sobre el
   archivo original sin ambigüedad (`DIE-F1-012`).

Para Markdown la unidad natural es la sección: un encabezado `##` y su cuerpo.
Cortar por número de caracteres a ciegas parte tablas y listas por la mitad, y
un requisito partido en dos fragmentos deja de poder citarse entero.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Un encabezado Markdown de nivel 1 a 3 al inicio de línea.
_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)

# Límite superior de una sección antes de partirla. No es un objetivo sino un
# tope: las secciones se respetan mientras quepan.
MAX_CHUNK_CHARS = 1800

# Por debajo de este tamaño, una sección se fusiona con la siguiente: un
# fragmento de dos líneas no sostiene ningún claim por sí solo.
MIN_CHUNK_CHARS = 180


@dataclass(frozen=True)
class TextChunk:
    """Fragmento con su posición exacta dentro del texto original."""

    ordinal: int
    heading: str | None
    text: str
    char_start: int
    char_end: int

    def __post_init__(self) -> None:
        if self.char_end <= self.char_start:
            raise ValueError(
                f"offsets inválidos en el fragmento {self.ordinal}: "
                f"char_end ({self.char_end}) debe ser mayor que char_start ({self.char_start})"
            )


@dataclass(frozen=True)
class _Section:
    heading: str | None
    level: int
    start: int
    end: int


def _sections(text: str) -> list[_Section]:
    """Secciones delimitadas por encabezados, en orden de aparición.

    El preámbulo anterior al primer encabezado también es una sección, con
    encabezado nulo: descartarlo perdería el texto introductorio.
    """
    matches = list(_HEADING.finditer(text))
    if not matches:
        return [_Section(heading=None, level=0, start=0, end=len(text))]

    sections: list[_Section] = []
    first = matches[0]
    if first.start() > 0 and text[: first.start()].strip():
        sections.append(_Section(heading=None, level=0, start=0, end=first.start()))

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append(
            _Section(
                heading=match.group(2),
                level=len(match.group(1)),
                start=match.start(),
                end=end,
            )
        )
    return sections


def _split_oversized(section: _Section, text: str) -> list[_Section]:
    """Parte una sección demasiado larga por párrafos, nunca a media frase."""
    body = text[section.start : section.end]
    if len(body.strip()) <= MAX_CHUNK_CHARS:
        return [section]

    pieces: list[_Section] = []
    cursor = section.start
    budget_end = cursor
    for paragraph in re.finditer(r"\n\s*\n", body):
        absolute = section.start + paragraph.end()
        if absolute - cursor >= MAX_CHUNK_CHARS:
            pieces.append(
                _Section(
                    heading=section.heading,
                    level=section.level,
                    start=cursor,
                    end=budget_end or absolute,
                )
            )
            cursor = budget_end or absolute
        budget_end = absolute
    if cursor < section.end:
        pieces.append(
            _Section(heading=section.heading, level=section.level, start=cursor, end=section.end)
        )
    return pieces or [section]


def _absorbs_into_next(section: _Section, text: str) -> bool:
    """¿Esta sección debe fundirse con la siguiente en lugar de ser citable?

    Dos casos, por motivos distintos:

    - **El título del documento (`#`) y el preámbulo.** Un `H1` con el nombre
      del trámite y un aviso de contenido sintético no es evidencia de nada,
      pero repite el vocabulario del documento entero: suelto, compite por el
      primer puesto de casi cualquier consulta sobre ese trámite y no puede
      sostener ni un requisito.
    - **Las secciones diminutas.** Un fragmento de dos líneas no sostiene un
      claim por sí solo.
    """
    if section.level == 1 or section.level == 0:
        return True
    return len(text[section.start : section.end].strip()) < MIN_CHUNK_CHARS


def _merge_stubs(sections: list[_Section], text: str) -> list[_Section]:
    """Funde títulos y secciones diminutas con la **siguiente** sección.

    Se conserva el encabezado de la sección siguiente, no el de la absorbida:
    la siguiente es la que trae el contenido, y su encabezado es el que describe
    lo que el fragmento afirma. Al revés —fundir hacia atrás conservando el
    encabezado anterior— se perdería el nombre de secciones sustantivas como
    «Zonificación aplicable a giros de alimentos», que dejarían de poder
    citarse por su nombre.
    """
    merged: list[_Section] = []
    pending_start: int | None = None

    for section in sections:
        start = pending_start if pending_start is not None else section.start
        if _absorbs_into_next(section, text) and section is not sections[-1]:
            pending_start = start
            continue
        merged.append(
            _Section(
                heading=section.heading,
                level=section.level,
                start=start,
                end=section.end,
            )
        )
        pending_start = None

    # Si la última sección quedó pendiente, se adjunta a la anterior: no hay
    # «siguiente» con la que fundirla.
    if pending_start is not None:
        if merged:
            last = merged.pop()
            merged.append(
                _Section(
                    heading=last.heading,
                    level=last.level,
                    start=last.start,
                    end=sections[-1].end,
                )
            )
        else:
            merged.append(sections[-1])
    return merged


def chunk_markdown(text: str) -> list[TextChunk]:
    """Fragmenta un documento Markdown en secciones citables.

    Los offsets son sobre el texto **original** recibido, sin normalizar: una
    citación debe poder resaltarse sobre el archivo tal como está en el
    repositorio.
    """
    sections: list[_Section] = []
    for section in _sections(text):
        sections.extend(_split_oversized(section, text))
    sections = _merge_stubs(sections, text)

    chunks: list[TextChunk] = []
    for ordinal, section in enumerate(sections):
        body = text[section.start : section.end]
        stripped = body.strip()
        if not stripped:
            continue
        # Los offsets apuntan al texto útil, no al espacio en blanco de relleno.
        offset = section.start + (len(body) - len(body.lstrip()))
        chunks.append(
            TextChunk(
                ordinal=ordinal,
                heading=section.heading,
                text=stripped,
                char_start=offset,
                char_end=offset + len(stripped),
            )
        )
    return chunks


CHUNKERS = {"text/markdown": chunk_markdown}
"""Estrategia por tipo documental. Un tipo no registrado se rechaza en la ingesta."""


def chunk_document(text: str, *, media_type: str) -> list[TextChunk]:
    try:
        chunker = CHUNKERS[media_type]
    except KeyError:
        raise ValueError(
            f"no hay estrategia de chunking para {media_type!r}; los tipos soportados son "
            f"{sorted(CHUNKERS)}"
        ) from None
    return chunker(text)
