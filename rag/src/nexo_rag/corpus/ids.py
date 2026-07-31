"""Identificadores deterministas de fragmentos.

Un `fragment_id` viaja dentro de cada citación y debe cumplir dos cosas a la
vez: ser **opaco** (no transporta significado ni PII, §2 de las convenciones) y
ser **estable** (el mismo documento en la misma versión produce siempre el mismo
identificador). Lo segundo es lo que hace idempotente la reingesta y lo que
permite que una citación emitida ayer siga apuntando al mismo texto hoy.

Se derivan de un hash sobre un alfabeto **sin dígitos**. No es una manía
estética: el validador de IDs rechaza secuencias largas de dígitos porque
parecen teléfonos o CURP, y un hash hexadecimal puede producir una por azar. Un
alfabeto de solo letras hace ese fallo imposible en lugar de improbable.
"""

from __future__ import annotations

import hashlib

# 24 letras: se omiten `l` y `o` porque se confunden con `1` y `0` al leer una
# traza a mano.
_ALPHABET = "abcdefghijkmnpqrstuvwxyz"
_LENGTH = 16


def stable_suffix(*parts: str) -> str:
    """Sufijo opaco y determinista derivado de las partes recibidas.

    El separador `\\x1f` no puede aparecer en ninguna de las partes, así que
    `("a", "bc")` y `("ab", "c")` no colisionan.
    """
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).digest()
    value = int.from_bytes(digest, "big")
    letters: list[str] = []
    for _ in range(_LENGTH):
        value, index = divmod(value, len(_ALPHABET))
        letters.append(_ALPHABET[index])
    return "".join(letters)


def chunk_id(source_id: str, document_id: str, version: str, ordinal: int) -> str:
    """Identificador de la unidad **indexada**, derivado de su posición.

    El ordinal es correcto aquí: si el chunking cambia, el índice cambia, y es
    deseable que los identificadores del índice lo reflejen.
    """
    return f"chunk_{stable_suffix(source_id, document_id, version, str(ordinal))}"


def fragment_id(
    source_id: str, document_id: str, version: str, heading: str | None, occurrence: int = 0
) -> str:
    """Identificador de la unidad **citable**, derivado de su encabezado.

    `fragment_id` y `chunk_id` son dos espacios de nombres distintos y se
    derivan de cosas distintas a propósito.

    Deriva del encabezado y no del ordinal porque un `fragment_id` viaja dentro
    de cada `SourceCitation` emitida, y esas citaciones ya están en respuestas
    entregadas, en fixtures y en datasets de evaluación. Con el ordinal, añadir
    una sección al principio de un documento —o ajustar el tamaño mínimo de
    fragmento— renumera todo lo que viene después y **invalida en silencio**
    todas las citaciones previas: siguen validando, siguen apuntando a un
    fragmento que existe, y ese fragmento ya no dice lo que decía.

    Con el encabezado, editar una sección no toca el identificador de las demás.
    `occurrence` desempata encabezados repetidos dentro del mismo documento.
    """
    suffix = stable_suffix(
        "fragment", source_id, document_id, version, heading or "", str(occurrence)
    )
    return f"frag_{suffix}"
