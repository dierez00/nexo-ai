"""Identificadores opacos con prefijo (`DIE-F0-008`, `DIE-F0-014`).

Un ID de Nexo IA es `<prefijo>_<cuerpo>`. El cuerpo es opaco: no transporta
significado ni datos personales, y ningún consumidor debe parsearlo para
deducir información. Los prefijos son cerrados para que un ID mal enrutado
falle en validación en vez de propagarse silenciosamente al módulo equivocado.
"""

from __future__ import annotations

import re
from typing import Annotated, Final, cast

from pydantic import AfterValidator, Field
from pydantic.fields import FieldInfo

# Prefijos registrados. Añadir uno es un cambio aditivo; renombrarlo o quitarlo
# obliga a una versión nueva de contratos.
ID_PREFIXES: Final[dict[str, str]] = {
    "usr": "usuario",
    "inst": "institución",
    "conv": "conversación",
    "msg": "mensaje",
    "run": "ejecución",
    "trace": "traza distribuida",
    "task": "tarea de agente",
    "evt": "evento de run",
    "chk": "checkpoint",
    "act": "acción confirmable",
    "apt": "cita",
    "fact": "hecho candidato o verificado",
    "src": "fuente documental",
    "doc": "documento",
    "frag": "fragmento citable",
    "chunk": "fragmento indexado",
    "tool": "tool registrada",
    "tc": "invocación de tool",
    "mdl": "invocación de modelo",
    "surf": "superficie A2UI",
    "skill": "skill operativa",
    "eval": "evaluación",
    "contra": "contradicción",
    "intg": "integración del MCP Mapper",
}

_BODY = r"[A-Za-z0-9][A-Za-z0-9_-]{0,62}"
_LONG_DIGIT_RUN = re.compile(r"\d{10,}")


def _make_id_validator(prefix: str) -> AfterValidator:
    pattern = re.compile(rf"^{re.escape(prefix)}_{_BODY}$")

    def _validate(value: str) -> str:
        if not pattern.match(value):
            raise ValueError(
                f"identificador inválido: se esperaba el prefijo '{prefix}_' seguido de "
                f"1 a 63 caracteres alfanuméricos, '_' o '-'; se recibió {value!r}"
            )
        # Un ID opaco no debe cargar PII incrustada. No podemos probarlo en
        # general, pero sí rechazar las formas obvias (`DIE-F0-009`).
        if "@" in value:
            raise ValueError(f"identificador no opaco: contiene '@' y parece un correo: {value!r}")
        if _LONG_DIGIT_RUN.search(value.removeprefix(f"{prefix}_")):
            raise ValueError(
                f"identificador no opaco: contiene una secuencia larga de dígitos que "
                f"podría ser un teléfono o una CURP: {value!r}"
            )
        return value

    return AfterValidator(_validate)


def _id_field(prefix: str) -> FieldInfo:
    """Restricciones de longitud del cuerpo, derivadas del prefijo."""
    if prefix not in ID_PREFIXES:
        raise KeyError(f"prefijo de ID no registrado: {prefix!r}")
    # `Field()` está declarado como `Any` en pydantic; el cast deja el tipo real.
    return cast(FieldInfo, Field(min_length=len(prefix) + 2, max_length=len(prefix) + 64))


# Los alias se escriben uno a uno en lugar de generarse con una fábrica.
#
# La fábrica era más corta y **rompía el análisis estático**: una función solo
# puede devolver un valor, no un tipo, así que `UserId = opaque_id("usr")` era
# `object` para el type checker y cualquier uso como anotación producía
# «Variable is not valid as a type». Eso invalidaba de golpe la comprobación de
# tipos de los ~24 identificadores del sistema, que son justamente los campos
# que más viajan entre módulos.
#
# Escritos así, `str` queda visible estáticamente y las restricciones siguen
# derivándose del prefijo en tiempo de ejecución: el JSON Schema publicado no
# cambia.
UserId = Annotated[str, _id_field("usr"), _make_id_validator("usr")]
InstitutionId = Annotated[str, _id_field("inst"), _make_id_validator("inst")]
ConversationId = Annotated[str, _id_field("conv"), _make_id_validator("conv")]
MessageId = Annotated[str, _id_field("msg"), _make_id_validator("msg")]
RunId = Annotated[str, _id_field("run"), _make_id_validator("run")]
TraceId = Annotated[str, _id_field("trace"), _make_id_validator("trace")]
TaskId = Annotated[str, _id_field("task"), _make_id_validator("task")]
EventId = Annotated[str, _id_field("evt"), _make_id_validator("evt")]
CheckpointId = Annotated[str, _id_field("chk"), _make_id_validator("chk")]
ActionId = Annotated[str, _id_field("act"), _make_id_validator("act")]
AppointmentId = Annotated[str, _id_field("apt"), _make_id_validator("apt")]
FactId = Annotated[str, _id_field("fact"), _make_id_validator("fact")]
SourceId = Annotated[str, _id_field("src"), _make_id_validator("src")]
DocumentId = Annotated[str, _id_field("doc"), _make_id_validator("doc")]
FragmentId = Annotated[str, _id_field("frag"), _make_id_validator("frag")]
ChunkId = Annotated[str, _id_field("chunk"), _make_id_validator("chunk")]
ToolId = Annotated[str, _id_field("tool"), _make_id_validator("tool")]
ToolCallId = Annotated[str, _id_field("tc"), _make_id_validator("tc")]
ModelInvocationId = Annotated[str, _id_field("mdl"), _make_id_validator("mdl")]
SurfaceId = Annotated[str, _id_field("surf"), _make_id_validator("surf")]
SkillId = Annotated[str, _id_field("skill"), _make_id_validator("skill")]
EvaluationId = Annotated[str, _id_field("eval"), _make_id_validator("eval")]
ContradictionId = Annotated[str, _id_field("contra"), _make_id_validator("contra")]
IntegrationId = Annotated[str, _id_field("intg"), _make_id_validator("intg")]

# La idempotency key la genera el cliente/backend y es un UUID, no un ID opaco
# con prefijo: se mantiene aparte para no confundir ambos espacios de nombres.
IdempotencyKey = Annotated[
    str,
    Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_\-]{7,127}$",
    ),
]
