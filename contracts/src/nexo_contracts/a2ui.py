"""Contratos de A2UI v0.9.1 (§5.5).

Excepción deliberada a la convención de wire format: el protocolo A2UI define
sus mensajes en `camelCase` (`createSurface`, `surfaceId`, `catalogId`), y aquí
se respeta el protocolo tal cual. Los campos Python siguen en `snake_case` y el
alias hace la traducción, de modo que el resto del sistema no cambia de estilo.

Nada de lo que se construye aquí se ejecuta: son estructuras declarativas
validadas contra un catálogo cerrado. HTML, JavaScript, SQL o código generado
por un modelo no tienen representación posible en estos contratos.
"""

from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import (
    ConfigDict,
    Field,
    JsonValue,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from .base import FrozenNexoModel, NexoModel
from .enums import A2UIMessageKind, A2UIValidationOutcome, Channel
from .ids import ActionId, SurfaceId
from .primitives import SemanticVersion
from .safety import SafePayload

A2UI_PROTOCOL_VERSION = "v0.9.1"

CatalogId = Annotated[
    str,
    Field(
        pattern=r"^urn:nexo-ia:a2ui:catalog:[a-z0-9_-]+:v\d+$",
        max_length=200,
        description="URN inmutable del catálogo negociado, por ejemplo "
        "'urn:nexo-ia:a2ui:catalog:citizen:v1'.",
    ),
]

ComponentId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,62}$")]

ROOT_COMPONENT_ID = "root"


class A2UIModel(NexoModel):
    """Base de los mensajes A2UI: cerrada y con alias `camelCase` del protocolo."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        alias_generator=lambda name: "".join(
            part if index == 0 else part.capitalize() for index, part in enumerate(name.split("_"))
        ),
    )

    def model_dump_wire(self, **kwargs: Any) -> dict[str, Any]:
        """Como el de `NexoModel`, pero omitiendo nulos.

        El protocolo A2UI espera una unidad JSON con exactamente la clave del
        mensaje presente; emitir `"updateComponents": null` junto a
        `"createSurface"` produce un mensaje que el renderer debe rechazar.
        """
        kwargs.setdefault("exclude_none", True)
        return super().model_dump_wire(**kwargs)

    def model_dump_json_wire(self, **kwargs: Any) -> str:
        kwargs.setdefault("exclude_none", True)
        return super().model_dump_json_wire(**kwargs)


class ComponentDescriptor(NexoModel):
    """Descriptor de un componente permitido dentro de un catálogo (§5.5)."""

    name: str = Field(pattern=r"^[A-Z][A-Za-z0-9]{1,40}$")
    schema_ref: str = Field(max_length=400)
    allows_children: bool = False
    is_interactive: bool = Field(
        default=False,
        description="Si puede emitir una acción; obliga a validar action_id y permiso.",
    )


class CatalogDescriptor(NexoModel):
    """Catálogo cerrado y versionado (§5.5).

    La allowlist es exhaustiva: un componente ausente de `components` no puede
    aparecer en ninguna superficie válida.
    """

    catalog_id: CatalogId
    version: SemanticVersion
    title: str = Field(max_length=200)
    audience: str = Field(max_length=40, description="'citizen' o 'admin'.")
    components: Annotated[list[ComponentDescriptor], Field(min_length=1, max_length=200)]

    def component_names(self) -> frozenset[str]:
        return frozenset(component.name for component in self.components)

    def find(self, name: str) -> ComponentDescriptor | None:
        return next((c for c in self.components if c.name == name), None)


class A2UIAction(FrozenNexoModel):
    """Acción opaca ligada a un schema, una versión y un run concreto (§5.5)."""

    action_id: ActionId
    tool_name: str = Field(max_length=95)
    input_schema_ref: str = Field(max_length=300)
    expected_version: int = Field(ge=1)
    requires_confirmation: bool = True
    label: str = Field(max_length=120)


_COMPONENT_DECLARED_KEYS = frozenset(
    {"id", "component", "children", "properties", "action_id", "actionId"}
)


class A2UIComponent(A2UIModel):
    """Nodo del árbol de componentes.

    Los datos viven en el data model y se referencian por binding (`{"path": ...}`);
    la estructura nunca los incrusta (`DIE-F1-102`).

    En el protocolo, las propiedades específicas del componente viajan aplanadas
    junto a `id` y `component`. Aquí se validan agrupadas bajo `properties` para
    mantener el modelo cerrado, y la (de)serialización hace la conversión: los
    fixtures que consume el renderer de Cris salen con la forma del protocolo,
    sin traducción implícita a cargo del consumidor (`DIE-F0-019`).
    """

    id: ComponentId
    component: str = Field(pattern=r"^[A-Z][A-Za-z0-9]{1,40}$")
    children: Annotated[list[ComponentId], Field(max_length=100)] = Field(default_factory=list)
    properties: SafePayload
    action_id: ActionId | None = None

    @model_validator(mode="before")
    @classmethod
    def _absorb_protocol_properties(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        extra = {key: value for key, value in data.items() if key not in _COMPONENT_DECLARED_KEYS}
        if not extra:
            return data
        absorbed = {key: value for key, value in data.items() if key in _COMPONENT_DECLARED_KEYS}
        merged: dict[str, Any] = dict(absorbed.get("properties") or {})
        merged.update(extra)
        absorbed["properties"] = merged
        return absorbed

    @model_serializer(mode="wrap")
    def _flatten_protocol_properties(
        self,
        handler: SerializerFunctionWrapHandler,
        info: SerializationInfo,
    ) -> Any:
        data = self.apply_wire_policy(handler(self), info)
        if not isinstance(data, dict):
            return data
        properties = data.pop("properties", None) or {}
        data.update(properties)
        return data


class CreateSurface(A2UIModel):
    surface_id: SurfaceId
    catalog_id: CatalogId
    send_data_model: bool = False


class UpdateDataModel(A2UIModel):
    surface_id: SurfaceId
    path: str = Field(pattern=r"^/[A-Za-z0-9_/-]*$", max_length=300)
    value: JsonValue


class UpdateComponents(A2UIModel):
    surface_id: SurfaceId
    components: Annotated[list[A2UIComponent], Field(min_length=1, max_length=200)]

    @model_validator(mode="after")
    def _exactly_one_root_and_resolvable_children(self) -> Self:
        ids = [component.id for component in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("hay identificadores de componente duplicados en el árbol")
        if ROOT_COMPONENT_ID not in ids:
            raise ValueError(
                f"el árbol debe declarar exactamente un componente '{ROOT_COMPONENT_ID}'"
            )
        known = set(ids)
        for component in self.components:
            missing = [child for child in component.children if child not in known]
            if missing:
                raise ValueError(
                    f"el componente {component.id!r} referencia hijos inexistentes: {missing}"
                )
        return self


class A2UIMessage(A2UIModel):
    """Unidad JSONL del protocolo: exactamente uno de los tres mensajes."""

    version: str = Field(default=A2UI_PROTOCOL_VERSION)
    create_surface: CreateSurface | None = None
    update_data_model: UpdateDataModel | None = None
    update_components: UpdateComponents | None = None

    @model_validator(mode="after")
    def _exactly_one_payload_and_pinned_version(self) -> Self:
        if self.version != A2UI_PROTOCOL_VERSION:
            raise ValueError(
                f"versión de protocolo no soportada: {self.version!r}; "
                f"Nexo IA fija {A2UI_PROTOCOL_VERSION}"
            )
        present = [
            name
            for name in ("create_surface", "update_data_model", "update_components")
            if getattr(self, name) is not None
        ]
        if len(present) != 1:
            raise ValueError(
                f"un mensaje A2UI debe transportar exactamente un payload; se recibieron "
                f"{len(present)}: {sorted(present)}"
            )
        return self

    @property
    def kind(self) -> A2UIMessageKind:
        if self.create_surface is not None:
            return A2UIMessageKind.CREATE_SURFACE
        if self.update_data_model is not None:
            return A2UIMessageKind.UPDATE_DATA_MODEL
        return A2UIMessageKind.UPDATE_COMPONENTS

    @property
    def surface_id(self) -> str:
        payload = self.create_surface or self.update_data_model or self.update_components
        assert payload is not None  # garantizado por el validador anterior
        return payload.surface_id


class A2UISurface(NexoModel):
    """Superficie completa: la secuencia ordenada de mensajes más sus acciones."""

    surface_id: SurfaceId
    catalog_id: CatalogId
    channel: Channel
    messages: Annotated[list[A2UIMessage], Field(min_length=1, max_length=100)]
    actions: Annotated[list[A2UIAction], Field(max_length=20)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _messages_are_coherent(self) -> Self:
        first = self.messages[0]
        if first.kind is not A2UIMessageKind.CREATE_SURFACE:
            raise ValueError(
                "la superficie debe abrir con `createSurface` antes de cualquier actualización"
            )
        assert first.create_surface is not None
        if first.create_surface.catalog_id != self.catalog_id:
            raise ValueError(
                f"el catálogo del mensaje ({first.create_surface.catalog_id!r}) no coincide "
                f"con el de la superficie ({self.catalog_id!r})"
            )
        for message in self.messages:
            if message.surface_id != self.surface_id:
                raise ValueError(
                    f"el mensaje apunta a la superficie {message.surface_id!r}, distinta de "
                    f"{self.surface_id!r}: `surfaceId` es inmutable"
                )
        return self

    @model_validator(mode="after")
    def _referenced_actions_are_declared(self) -> Self:
        """Un componente no puede disparar una acción que la superficie no declaró."""
        declared = {action.action_id for action in self.actions}
        for message in self.messages:
            if message.update_components is None:
                continue
            for component in message.update_components.components:
                if component.action_id is not None and component.action_id not in declared:
                    raise ValueError(
                        f"el componente {component.id!r} referencia la acción "
                        f"{component.action_id!r}, que la superficie no declara"
                    )
        return self


class A2UIValidationError(NexoModel):
    """Error de validación seguro: describe el problema sin filtrar el payload."""

    component_id: str | None = Field(default=None, max_length=63)
    rule: str = Field(max_length=100, description="Regla violada, en snake_case.")
    detail: str = Field(max_length=300)


class A2UIValidationResult(NexoModel):
    """Resultado de validar una superficie contra su catálogo (§5.5)."""

    surface_id: SurfaceId
    catalog_id: CatalogId
    outcome: A2UIValidationOutcome
    errors: Annotated[list[A2UIValidationError], Field(max_length=100)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def _invalid_results_explain_themselves(self) -> Self:
        if self.outcome is A2UIValidationOutcome.INVALID and not self.errors:
            raise ValueError("una validación inválida debe enumerar al menos un error")
        if self.outcome is A2UIValidationOutcome.VALID and self.errors:
            raise ValueError("una validación válida no puede reportar errores")
        return self

    @property
    def is_valid(self) -> bool:
        return self.outcome is A2UIValidationOutcome.VALID


class ChannelFallback(NexoModel):
    """Representación segura cuando la superficie no puede renderizarse (§5.5).

    Nunca queda vacío: si A2UI falla, el canal recibe texto plano equivalente en
    lugar de nada (`DIE-F1-106`).
    """

    channel: Channel
    reason: str = Field(max_length=200)
    text: str = Field(min_length=1, max_length=4000)
    numbered_items: Annotated[list[str], Field(max_length=50)] = Field(default_factory=list)
    action_hint: str | None = Field(default=None, max_length=300)
