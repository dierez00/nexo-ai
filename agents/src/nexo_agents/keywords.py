"""Normalización para coincidencia de palabras clave.

Se usa en el fallback determinista del clasificador. Es intencionadamente
distinta de la de `nexo_rag.retrieval.lexical`: aquí **no** se lematiza ni se
quitan palabras vacías, porque una palabra clave como «uso de suelo» es una
frase exacta y lematizarla la rompería.

Lo único que se normaliza es lo que la gente escribe de forma inconsistente:
mayúsculas, acentos y espacios repetidos.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")


def normalize_for_match(text: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados, más un espacio guarda.

    Los espacios al inicio y al final permiten buscar palabras completas: sin
    ellos, «debo» coincidiría dentro de «adebo» o de cualquier palabra que la
    contenga.
    """
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    collapsed = _WHITESPACE.sub(" ", stripped)
    # Los signos de puntuación se sustituyen por espacio, no se borran: «licencia,
    # y saber» debe seguir teniendo frontera de palabra entre las dos.
    punctuated = re.sub(r"[^\w\s]", " ", collapsed)
    return f" {_WHITESPACE.sub(' ', punctuated).strip()} "
