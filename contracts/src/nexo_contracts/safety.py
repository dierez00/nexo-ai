"""Tipos que hacen cumplir las invariantes de serialización y minimización.

`DIE-F0-015` exige que el estado sea serializable y no contenga clientes,
handles, corrutinas ni secretos. En Pydantic eso se consigue con dos piezas:

1. `JsonValue` como único tipo admitido en los campos de forma libre, lo que
   rechaza en validación cualquier objeto vivo (conexión, corrutina, lambda).
2. Un validador que rechaza claves con aspecto de secreto o de PII directa,
   aplicable a los diccionarios que viajan en eventos, parámetros y auditoría.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, Field, JsonValue

_SECRETISH_KEY = re.compile(
    r"(api[_-]?key|secret|password|passwd|token|authorization|bearer|credential|"
    r"private[_-]?key|session[_-]?id|cookie)",
    re.IGNORECASE,
)

_PII_KEY = re.compile(
    r"(curp|rfc|nss|telefono|phone|celular|email|correo|domicilio|direccion|"
    r"address|birth|nacimiento|placa|plate)",
    re.IGNORECASE,
)

MAX_FREEFORM_DEPTH = 6


def _walk_keys(value: JsonValue, depth: int = 0) -> list[str]:
    if depth > MAX_FREEFORM_DEPTH:
        raise ValueError(
            f"estructura de datos demasiado profunda: supera {MAX_FREEFORM_DEPTH} niveles, "
            f"lo que sugiere un payload no minimizado"
        )
    keys: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.append(key)
            keys.extend(_walk_keys(nested, depth + 1))
    elif isinstance(value, list):
        for nested in value:
            keys.extend(_walk_keys(nested, depth + 1))
    return keys


def reject_unsafe_keys(value: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Rechaza claves con aspecto de secreto o de PII directa (`DIE-F0-009`).

    Es una barrera sintáctica, no una garantía semántica: no puede detectar un
    secreto guardado bajo un nombre inocuo. Su función es que el caso descuidado
    y frecuente falle en validación, no en producción.
    """
    for key in _walk_keys(value):
        if _SECRETISH_KEY.search(key):
            raise ValueError(
                f"la clave {key!r} parece un secreto; los contratos transportan referencias "
                f"a secretos, nunca su valor"
            )
        if _PII_KEY.search(key):
            raise ValueError(
                f"la clave {key!r} parece PII directa; usa una referencia opaca "
                f"(por ejemplo 'pii_ref:...') en su lugar"
            )
    return value


SafePayload = Annotated[
    dict[str, JsonValue],
    Field(default_factory=dict),
    AfterValidator(reject_unsafe_keys),
]
"""Diccionario de forma libre, serializable, sin secretos ni PII directa.

Se usa en eventos, parámetros de tools, metadata y auditoría: todo lugar donde
el contrato no puede fijar la forma exacta pero sí debe garantizar que lo que
viaje sea JSON puro y minimizado.
"""
