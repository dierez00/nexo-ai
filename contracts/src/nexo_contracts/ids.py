"""Identificadores opacos con prefijo (`DIE-F0-008`, `DIE-F0-014`).

Un ID de Nexo IA es `<prefijo>_<cuerpo>`. El cuerpo es opaco: no transporta
significado ni datos personales, y ningún consumidor debe parsearlo para
deducir información. Los prefijos son cerrados para que un ID mal enrutado
falle en validación en vez de propagarse silenciosamente al módulo equivocado.
"""

from __future__ import annotations

import re
from typing import Annotated, Final

from pydantic import AfterValidator, Field

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


def opaque_id(prefix: str) -> object:
    """Construye el tipo anotado de un ID opaco con el prefijo indicado."""
    if prefix not in ID_PREFIXES:
        raise KeyError(f"prefijo de ID no registrado: {prefix!r}")
    return Annotated[
        str,
        Field(min_length=len(prefix) + 2, max_length=len(prefix) + 64),
        _make_id_validator(prefix),
    ]


UserId = opaque_id("usr")
InstitutionId = opaque_id("inst")
ConversationId = opaque_id("conv")
MessageId = opaque_id("msg")
RunId = opaque_id("run")
TraceId = opaque_id("trace")
TaskId = opaque_id("task")
EventId = opaque_id("evt")
CheckpointId = opaque_id("chk")
ActionId = opaque_id("act")
AppointmentId = opaque_id("apt")
FactId = opaque_id("fact")
SourceId = opaque_id("src")
DocumentId = opaque_id("doc")
FragmentId = opaque_id("frag")
ChunkId = opaque_id("chunk")
ToolId = opaque_id("tool")
ToolCallId = opaque_id("tc")
ModelInvocationId = opaque_id("mdl")
SurfaceId = opaque_id("surf")
SkillId = opaque_id("skill")
EvaluationId = opaque_id("eval")
ContradictionId = opaque_id("contra")
IntegrationId = opaque_id("intg")

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
