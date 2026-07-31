"""Base común de todos los contratos de Nexo IA.

Define la clase raíz `NexoModel` y la distinción entre campos *wire* (visibles
para cualquier consumidor del contrato) y campos *internos* (`DIE-F0-013`), que
existen en el estado serializado pero nunca deben salir hacia un canal, un
frontend o un reporte.

La exclusión de campos internos se resuelve con un serializador envolvente que
lee el `context` de Pydantic. El contexto se propaga a los modelos anidados, así
que `model_dump_wire()` limpia el árbol completo sin que cada contrato tenga que
reimplementarlo.
"""

from __future__ import annotations

from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from pydantic.fields import FieldInfo
from pydantic.json_schema import GetJsonSchemaHandler, JsonSchemaValue

# Revisión del conjunto de contratos. Los cambios aditivos conservan esta
# versión; eliminar o renombrar un campo exige publicar `v2` (`DIE-F0-007`).
CONTRACTS_SCHEMA_VERSION = "v1"

_VISIBILITY_KEY = "nexo_visibility"
_INTERNAL = "internal"
_WIRE_CONTEXT_FLAG = "wire"


def is_internal(field: FieldInfo) -> bool:
    """Indica si un campo está marcado como exclusivamente interno."""
    extra = field.json_schema_extra
    return isinstance(extra, dict) and extra.get(_VISIBILITY_KEY) == _INTERNAL


class NexoModel(BaseModel):
    """Modelo base: cerrado a propiedades desconocidas y consciente del wire format.

    `extra="forbid"` es deliberado y transversal: un payload con un campo no
    declarado es un error de contrato, no un dato que se ignora en silencio.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_default=True,
        use_enum_values=False,
    )

    @classmethod
    def internal_field_names(cls) -> frozenset[str]:
        """Nombres y alias de serialización de los campos internos de este modelo."""
        names: set[str] = set()
        for name, field in cls.model_fields.items():
            if is_internal(field):
                names.add(name)
                if field.serialization_alias:
                    names.add(field.serialization_alias)
                if field.alias:
                    names.add(field.alias)
        return frozenset(names)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: Any, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Excluye los campos internos del JSON Schema publicado.

        `model_json_schema(mode="serialization")` no puede introspeccionar
        `_strip_internal_fields` (un `model_serializer(mode="wrap")` sin tipo de
        retorno declarado), así que `export.py` genera el schema en modo
        `validation` y confía en este hook para aplicar la misma política de
        wire que `apply_wire_policy` aplica en tiempo de ejecución.
        """
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        internal = cls.internal_field_names()
        if internal and "properties" in json_schema:
            for name in list(json_schema["properties"]):
                if name in internal:
                    del json_schema["properties"][name]
            if "required" in json_schema:
                json_schema["required"] = [
                    name for name in json_schema["required"] if name not in internal
                ]
                if not json_schema["required"]:
                    del json_schema["required"]
        return json_schema

    def apply_wire_policy(self, data: Any, info: SerializationInfo) -> Any:
        """Elimina los campos internos cuando se serializa en modo wire.

        Se expone como método para que una subclase que necesite su propio
        `model_serializer` (por ejemplo A2UI, que aplana propiedades) siga
        aplicando esta política en lugar de perderla al sobrescribir.
        """
        context = info.context or {}
        if not context.get(_WIRE_CONTEXT_FLAG) or not isinstance(data, dict):
            return data
        for name in type(self).internal_field_names():
            data.pop(name, None)
        return data

    @model_serializer(mode="wrap")
    def _strip_internal_fields(
        self,
        handler: SerializerFunctionWrapHandler,
        info: SerializationInfo,
    ) -> Any:
        return self.apply_wire_policy(handler(self), info)

    def model_dump_wire(self, **kwargs: Any) -> dict[str, Any]:
        """Serializa solo lo publicable, en modo JSON y con alias de wire format."""
        context = {_WIRE_CONTEXT_FLAG: True, **(kwargs.pop("context", None) or {})}
        kwargs.setdefault("mode", "json")
        kwargs.setdefault("by_alias", True)
        return self.model_dump(context=context, **kwargs)

    def model_dump_json_wire(self, **kwargs: Any) -> str:
        """Equivalente a `model_dump_wire` devolviendo JSON serializado."""
        context = {_WIRE_CONTEXT_FLAG: True, **(kwargs.pop("context", None) or {})}
        kwargs.setdefault("by_alias", True)
        return self.model_dump_json(context=context, **kwargs)

    def round_trip(self) -> Self:
        """Revalida el modelo desde su propia serialización JSON completa.

        Es la operación que ejercen los contract tests de `DIE-F0-018`: si un
        contrato no sobrevive su propio round-trip, no es transportable.
        """
        return type(self).model_validate_json(self.model_dump_json(by_alias=True))


class FrozenNexoModel(NexoModel):
    """Contrato inmutable, para snapshots que no pueden mutar después de creados."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_default=True,
        use_enum_values=False,
        frozen=True,
    )
