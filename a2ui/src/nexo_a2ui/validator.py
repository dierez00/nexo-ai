"""Validación de superficies contra el catálogo cerrado (`DIE-F1-104`, `DIE-F1-105`).

El contrato `A2UISurface` ya garantiza la forma: un `createSurface` primero, un
único `root`, hijos resolubles, acciones declaradas. Lo que **no** puede
garantizar es lo que depende del catálogo, porque el catálogo es configuración:

- que cada componente exista en la allowlist;
- que cada propiedad exista para ese componente (cierra `TD-04` de Fase 0);
- que solo un componente interactivo dispare una acción;
- que la acción pertenezca a este run y no a otro (`DIE-F1-105`).

Los errores se devuelven describiendo la regla violada, nunca el payload: un
mensaje de validación que incluye lo que falló puede filtrar exactamente lo que
un atacante quería ver.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import JsonValue

from nexo_contracts import (
    A2UIComponent,
    A2UIMessageKind,
    A2UISurface,
    A2UIValidationError,
    A2UIValidationOutcome,
    A2UIValidationResult,
    CatalogDescriptor,
)

from .catalog import ALLOWED_PROPERTIES, ALLOWED_TONES

# Esquemas de URL admitidos en cualquier propiedad que parezca un enlace. Todo
# lo demás —`javascript:`, `data:`, `file:`— se rechaza: son los vectores
# clásicos de ejecución dentro de un renderer.
ALLOWED_URL_SCHEMES = frozenset({"https"})

_URL_PROPERTY_HINTS = ("url", "href", "link")


@dataclass
class SurfaceValidator:
    """Valida superficies contra un catálogo concreto."""

    catalog: CatalogDescriptor
    allowed_properties: dict[str, frozenset[str]] = field(
        default_factory=lambda: dict(ALLOWED_PROPERTIES)
    )

    def validate(
        self, surface: A2UISurface, *, run_action_ids: frozenset[str] | None = None
    ) -> A2UIValidationResult:
        """Valida una superficie. `run_action_ids` acota las acciones a este run."""
        errors: list[A2UIValidationError] = []

        if surface.catalog_id != self.catalog.catalog_id:
            errors.append(
                A2UIValidationError(
                    rule="unknown_catalog",
                    detail=(
                        f"la superficie declara un catálogo que este servidor no publica; "
                        f"se esperaba {self.catalog.catalog_id!r}"
                    ),
                )
            )
            # Sin catálogo coincidente no tiene sentido seguir: cualquier
            # componente sería «desconocido» y el informe sería ilegible.
            return _result(surface, errors)

        known = self.catalog.component_names()
        data_model = self._data_model(surface)
        for message in surface.messages:
            if message.kind is not A2UIMessageKind.UPDATE_COMPONENTS:
                continue
            assert message.update_components is not None
            for component in message.update_components.components:
                errors.extend(self._validate_component(component, known, data_model))

        errors.extend(self._validate_actions(surface, run_action_ids))
        return _result(surface, errors)

    # -- componente ---------------------------------------------------------

    def _validate_component(
        self,
        component: A2UIComponent,
        known: frozenset[str],
        data_model: JsonValue,
    ) -> list[A2UIValidationError]:
        errors: list[A2UIValidationError] = []

        if component.component not in known:
            errors.append(
                A2UIValidationError(
                    component_id=component.id,
                    rule="component_not_in_catalog",
                    detail=f"el componente {component.component!r} no está en el catálogo",
                )
            )
            return errors

        descriptor = self.catalog.find(component.component)
        assert descriptor is not None

        if component.children and not descriptor.allows_children:
            errors.append(
                A2UIValidationError(
                    component_id=component.id,
                    rule="children_not_allowed",
                    detail=f"{component.component!r} no admite hijos",
                )
            )

        allowed = self.allowed_properties.get(component.component, frozenset())
        unknown = sorted(set(component.properties) - allowed)
        if unknown:
            errors.append(
                A2UIValidationError(
                    component_id=component.id,
                    rule="unknown_property",
                    detail=(
                        f"{component.component!r} no admite las propiedades {unknown}; "
                        f"admite {sorted(allowed)}"
                    ),
                )
            )

        errors.extend(self._validate_property_values(component))
        for path in _binding_paths(component.properties):
            if not _path_exists(data_model, path):
                errors.append(
                    A2UIValidationError(
                        component_id=component.id,
                        rule="binding_path_not_found",
                        detail="el binding referencia una ruta ausente del data model",
                    )
                )

        # `DIE-F1-105`: solo un componente declarado interactivo puede disparar
        # una acción. Sin esto, un `Text` con `actionId` sería un botón invisible.
        if component.action_id is not None and not descriptor.is_interactive:
            errors.append(
                A2UIValidationError(
                    component_id=component.id,
                    rule="action_on_non_interactive_component",
                    detail=f"{component.component!r} no es interactivo y declara una acción",
                )
            )
        return errors

    @staticmethod
    def _data_model(surface: A2UISurface) -> JsonValue:
        """Reconstruye el modelo raíz que precede al árbol del MVP."""
        data_model: JsonValue = {}
        for message in surface.messages:
            update = message.update_data_model
            if update is not None and update.path == "/":
                data_model = update.value
        return data_model

    def _validate_property_values(self, component: A2UIComponent) -> list[A2UIValidationError]:
        errors: list[A2UIValidationError] = []
        for name, value in component.properties.items():
            if name == "tone" and value not in ALLOWED_TONES:
                errors.append(
                    A2UIValidationError(
                        component_id=component.id,
                        rule="unknown_tone",
                        detail=f"tono no permitido; los válidos son {sorted(ALLOWED_TONES)}",
                    )
                )
            if any(hint in name.lower() for hint in _URL_PROPERTY_HINTS) and isinstance(value, str):
                scheme = value.split(":", 1)[0].lower() if ":" in value else ""
                if scheme not in ALLOWED_URL_SCHEMES:
                    errors.append(
                        A2UIValidationError(
                            component_id=component.id,
                            rule="unsafe_url_scheme",
                            detail=(
                                f"la propiedad {name!r} usa un esquema no permitido; "
                                f"solo se admite {sorted(ALLOWED_URL_SCHEMES)}"
                            ),
                        )
                    )
        return errors

    # -- acciones -----------------------------------------------------------

    def _validate_actions(
        self, surface: A2UISurface, run_action_ids: frozenset[str] | None
    ) -> list[A2UIValidationError]:
        """Comprueba que las acciones sean de este run y estén enlazadas.

        `run_action_ids` es la lista de acciones que el supervisor autorizó para
        **este** run. Sin ella, una superficie podría declarar una acción con un
        `action_id` válido de otro run y el renderer la mostraría como legítima.
        """
        errors: list[A2UIValidationError] = []

        if run_action_ids is not None:
            foreign = sorted(
                action.action_id
                for action in surface.actions
                if action.action_id not in run_action_ids
            )
            if foreign:
                errors.append(
                    A2UIValidationError(
                        rule="action_not_authorised_for_run",
                        detail=(
                            f"la superficie declara {len(foreign)} acción(es) que no "
                            f"pertenecen a este run"
                        ),
                    )
                )

        for action in surface.actions:
            if not action.requires_confirmation:
                errors.append(
                    A2UIValidationError(
                        rule="action_without_confirmation",
                        detail=(
                            "una acción de la superficie ciudadana debe exigir "
                            "confirmación explícita"
                        ),
                    )
                )

        # Una acción declarada y no enlazada a ningún componente es un botón que
        # nadie puede pulsar; no rompe nada, pero indica una superficie mal
        # construida y conviene verlo en la traza.
        bound = {
            component.action_id
            for message in surface.messages
            if message.update_components is not None
            for component in message.update_components.components
            if component.action_id is not None
        }
        orphan = sorted(
            action.action_id for action in surface.actions if action.action_id not in bound
        )
        if orphan:
            errors.append(
                A2UIValidationError(
                    rule="declared_action_is_unreachable",
                    detail=(
                        f"{len(orphan)} acción(es) declaradas no están enlazadas a "
                        f"ningún componente"
                    ),
                )
            )
        return errors


def _result(surface: A2UISurface, errors: list[A2UIValidationError]) -> A2UIValidationResult:
    return A2UIValidationResult(
        surface_id=surface.surface_id,
        catalog_id=surface.catalog_id,
        outcome=A2UIValidationOutcome.INVALID if errors else A2UIValidationOutcome.VALID,
        errors=errors,
    )


def _binding_paths(value: JsonValue) -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str):
            paths.append(path)
        for child in value.values():
            paths.extend(_binding_paths(child))
    elif isinstance(value, list):
        for child in value:
            paths.extend(_binding_paths(child))
    return tuple(paths)


def _path_exists(data_model: JsonValue, path: str) -> bool:
    if path == "/":
        return True
    if not path.startswith("/"):
        return False
    current = data_model
    for part in path.removeprefix("/").split("/"):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
            continue
        return False
    return True
