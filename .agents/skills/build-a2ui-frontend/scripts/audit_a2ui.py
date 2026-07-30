#!/usr/bin/env python3
"""Audit Nexo A2UI v0.9.1 catalogs and JSONL fixtures without dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


PROTOCOL_VERSION = "v0.9.1"
BASIC_COMPONENTS = {
    "Text",
    "Image",
    "Icon",
    "Video",
    "AudioPlayer",
    "Row",
    "Column",
    "List",
    "Card",
    "Tabs",
    "Divider",
    "Modal",
    "Button",
    "CheckBox",
    "TextField",
    "DateTimeInput",
    "ChoicePicker",
    "Slider",
}
MESSAGE_TYPES = {
    "createSurface",
    "updateComponents",
    "updateDataModel",
    "deleteSurface",
}
FORBIDDEN_KEYS = {
    "className",
    "style",
    "dangerouslySetInnerHTML",
    "html",
    "innerHTML",
    "script",
    "handler",
    "module",
}
EVENT_NAME = re.compile(r"^[a-z][a-z0-9_.-]{2,127}$")
COMPONENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
RELATIVE_POINTER = re.compile(r"^[A-Za-z0-9_~.-]+(?:/[A-Za-z0-9_~.-]+)*$")


class AuditError(ValueError):
    pass


@dataclass(frozen=True)
class Catalog:
    path: Path
    catalog_id: str
    components: frozenset[str]
    functions: frozenset[str]


@dataclass
class Surface:
    surface_id: str
    catalog: Catalog
    components: dict[str, dict[str, Any]] = field(default_factory=dict)
    references: dict[str, set[str]] = field(default_factory=dict)


def fail(location: str, message: str) -> None:
    raise AuditError(f"{location}: {message}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AuditError(f"{path}: no se pudo leer: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(f"{path}:{exc.lineno}: JSON inválido: {exc.msg}") from exc
    if not isinstance(value, dict):
        fail(str(path), "la raíz debe ser un objeto JSON")
    return value


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AuditError(f"{path}: no se pudo leer: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{path}:{line_number}", f"JSONL inválido: {exc.msg}")
        if not isinstance(value, dict):
            fail(f"{path}:{line_number}", "cada línea debe contener un objeto")
        yield line_number, value


def validate_catalog(path: Path) -> Catalog:
    data = load_json(path)
    catalog_id = data.get("catalogId")
    if not isinstance(catalog_id, str) or not catalog_id:
        fail(str(path), "catalogId es obligatorio")
    if data.get("$id") != catalog_id:
        fail(str(path), "$id debe coincidir exactamente con catalogId")

    components = data.get("components")
    functions = data.get("functions")
    if not isinstance(components, dict) or not components:
        fail(str(path), "components debe ser un objeto no vacío")
    if not isinstance(functions, dict) or not functions:
        fail(str(path), "functions debe ser un objeto no vacío")

    component_names = frozenset(components)
    missing = BASIC_COMPONENTS - component_names
    if missing:
        fail(str(path), f"faltan componentes básicos: {', '.join(sorted(missing))}")

    for name, schema in components.items():
        location = f"{path}#/components/{name}"
        if not isinstance(schema, dict):
            fail(location, "el schema debe ser un objeto")
        if name not in BASIC_COMPONENTS:
            if schema.get("unevaluatedProperties") is not False:
                fail(location, "los componentes propios deben cerrar unevaluatedProperties")
            validate_schema_security(schema, location)

    defs = data.get("$defs")
    if not isinstance(defs, dict) or not isinstance(defs.get("anyComponent"), dict):
        fail(str(path), "$defs.anyComponent es obligatorio")

    serialized_refs = json.dumps(defs["anyComponent"], ensure_ascii=False)
    for name in component_names:
        if f"#/components/{name}" not in serialized_refs:
            fail(str(path), f"$defs.anyComponent no incluye {name}")

    return Catalog(
        path=path,
        catalog_id=catalog_id,
        components=component_names,
        functions=frozenset(functions),
    )


def validate_schema_security(value: Any, location: str) -> None:
    if isinstance(value, dict):
        if value.get("additionalProperties") is True:
            fail(location, "additionalProperties:true abre el contrato")
        for key, child in value.items():
            if key in {"child", "trigger", "content"} and isinstance(child, dict):
                ref = child.get("$ref", "")
                if "ComponentId" not in ref:
                    fail(location, f"{key} debe referenciar ComponentId")
            if key == "children" and isinstance(child, dict):
                ref = child.get("$ref", "")
                if "ChildList" not in ref:
                    fail(location, "children debe referenciar ChildList")
            validate_schema_security(child, f"{location}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_schema_security(child, f"{location}/{index}")


def validate_pointer(path: str, location: str) -> None:
    if not path or ".." in path:
        fail(location, "binding path vacío o inseguro")
    if path.startswith("/"):
        return
    if not RELATIVE_POINTER.fullmatch(path):
        fail(location, "binding relativo inválido")


def validate_url(value: str, location: str, allowed_hosts: set[str]) -> None:
    lowered = value.strip().lower()
    if lowered.startswith(("javascript:", "data:text/html", "vbscript:")):
        fail(location, "protocolo URL inseguro")
    if value.startswith("/") and not value.startswith("//"):
        return
    parsed = urlparse(value)
    if not parsed.scheme:
        return
    if parsed.scheme != "https":
        fail(location, "solo se permiten URLs https o relativas")
    if parsed.hostname and parsed.hostname.lower() not in allowed_hosts:
        fail(location, f"host URL no permitido: {parsed.hostname}")


def validate_action(
    value: Any,
    location: str,
    catalog: Catalog,
    allowed_hosts: set[str],
) -> None:
    if not isinstance(value, dict):
        fail(location, "action debe ser un objeto")
    variants = [key for key in ("event", "functionCall") if key in value]
    if len(variants) != 1 or len(value) != 1:
        fail(location, "action debe contener exactamente event o functionCall")

    if "event" in value:
        event = value["event"]
        if not isinstance(event, dict):
            fail(location, "event debe ser un objeto")
        if set(event) - {"name", "context"}:
            fail(location, "event contiene propiedades no permitidas")
        name = event.get("name")
        if not isinstance(name, str) or not EVENT_NAME.fullmatch(name):
            fail(location, "nombre de evento inválido")
        context = event.get("context", {})
        if not isinstance(context, dict):
            fail(location, "event.context debe ser un objeto")
        validate_payload(context, f"{location}/event/context", catalog, allowed_hosts)
        return

    function_call = value["functionCall"]
    validate_function_call(function_call, f"{location}/functionCall", catalog, allowed_hosts)


def validate_function_call(
    value: Any,
    location: str,
    catalog: Catalog,
    allowed_hosts: set[str],
) -> None:
    if not isinstance(value, dict):
        fail(location, "functionCall debe ser un objeto")
    call = value.get("call")
    if not isinstance(call, str) or call not in catalog.functions:
        fail(location, f"función no registrada: {call!r}")
    args = value.get("args", {})
    if not isinstance(args, dict):
        fail(location, "functionCall.args debe ser un objeto")
    validate_payload(args, f"{location}/args", catalog, allowed_hosts)


def validate_payload(
    value: Any,
    location: str,
    catalog: Catalog,
    allowed_hosts: set[str],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS or re.match(r"^on[A-Z_]", key):
                fail(location, f"propiedad insegura: {key}")
            if key == "action":
                validate_action(child, f"{location}/action", catalog, allowed_hosts)
                continue
            if key == "functionCall":
                validate_function_call(
                    child,
                    f"{location}/functionCall",
                    catalog,
                    allowed_hosts,
                )
                continue
            if key == "call":
                validate_function_call(value, location, catalog, allowed_hosts)
                return
            if key == "path":
                if not isinstance(child, str):
                    fail(location, "path debe ser string")
                validate_pointer(child, f"{location}/path")
            if key.lower().endswith("url") and isinstance(child, str):
                validate_url(child, f"{location}/{key}", allowed_hosts)
            validate_payload(child, f"{location}/{key}", catalog, allowed_hosts)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_payload(child, f"{location}/{index}", catalog, allowed_hosts)
    elif isinstance(value, str):
        lowered = value.lower()
        if "<script" in lowered or "javascript:" in lowered:
            fail(location, "contenido ejecutable detectado")


def collect_references(component: dict[str, Any], location: str) -> set[str]:
    references: set[str] = set()

    for key in ("child", "trigger", "content"):
        if key in component:
            child = component[key]
            if not isinstance(child, str) or not COMPONENT_ID.fullmatch(child):
                fail(location, f"{key} debe ser un ComponentId válido")
            references.add(child)

    children = component.get("children")
    if isinstance(children, list):
        for child in children:
            if not isinstance(child, str) or not COMPONENT_ID.fullmatch(child):
                fail(location, "children contiene un ComponentId inválido")
            references.add(child)
    elif isinstance(children, dict):
        child = children.get("componentId")
        path = children.get("path")
        if not isinstance(child, str) or not COMPONENT_ID.fullmatch(child):
            fail(location, "template children requiere componentId válido")
        if not isinstance(path, str):
            fail(location, "template children requiere path")
        validate_pointer(path, f"{location}/children/path")
        references.add(child)
    elif children is not None:
        fail(location, "children debe ser array o template")

    tabs = component.get("tabs")
    if isinstance(tabs, list):
        for index, tab in enumerate(tabs):
            if not isinstance(tab, dict) or not isinstance(tab.get("child"), str):
                fail(f"{location}/tabs/{index}", "tab requiere child")
            references.add(tab["child"])

    return references


def validate_surface(surface: Surface, location: str) -> None:
    if "root" not in surface.components:
        fail(location, f"surface {surface.surface_id!r} no contiene root")

    known = set(surface.components)
    for parent, references in surface.references.items():
        missing = references - known
        if missing:
            fail(
                location,
                f"{parent} referencia componentes ausentes: {', '.join(sorted(missing))}",
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(component_id: str) -> None:
        if component_id in visiting:
            fail(location, f"ciclo en el árbol de componentes desde {component_id}")
        if component_id in visited:
            return
        visiting.add(component_id)
        for child in surface.references.get(component_id, set()):
            visit(child)
        visiting.remove(component_id)
        visited.add(component_id)

    visit("root")


def audit_fixture(
    path: Path,
    catalogs: dict[str, Catalog],
    allowed_hosts: set[str],
) -> None:
    surfaces: dict[str, Surface] = {}
    retired: set[str] = set()
    message_count = 0

    for line_number, message in iter_jsonl(path):
        message_count += 1
        location = f"{path}:{line_number}"
        if message.get("version") != PROTOCOL_VERSION:
            fail(location, f"version debe ser {PROTOCOL_VERSION}")
        message_types = MESSAGE_TYPES.intersection(message)
        if len(message_types) != 1 or set(message) != {"version", *message_types}:
            fail(location, "cada mensaje debe contener un único tipo de envelope")
        message_type = next(iter(message_types))
        payload = message[message_type]
        if not isinstance(payload, dict):
            fail(location, f"{message_type} debe ser un objeto")

        surface_id = payload.get("surfaceId")
        if not isinstance(surface_id, str) or not COMPONENT_ID.fullmatch(surface_id):
            fail(location, "surfaceId inválido")

        if message_type == "createSurface":
            if surface_id in surfaces or surface_id in retired:
                fail(location, "surfaceId recreado o duplicado")
            catalog_id = payload.get("catalogId")
            catalog = catalogs.get(catalog_id)
            if catalog is None:
                fail(location, f"catálogo desconocido: {catalog_id!r}")
            validate_payload(payload, location, catalog, allowed_hosts)
            surfaces[surface_id] = Surface(surface_id, catalog)
            continue

        surface = surfaces.get(surface_id)
        if surface is None:
            fail(location, "actualización para una surface no creada o eliminada")

        if message_type == "deleteSurface":
            validate_surface(surface, location)
            del surfaces[surface_id]
            retired.add(surface_id)
            continue

        validate_payload(payload, location, surface.catalog, allowed_hosts)

        if message_type == "updateComponents":
            components = payload.get("components")
            if not isinstance(components, list) or not components:
                fail(location, "components debe ser un array no vacío")
            ids_in_message: set[str] = set()
            for index, component in enumerate(components):
                component_location = f"{location}/components/{index}"
                if not isinstance(component, dict):
                    fail(component_location, "el componente debe ser un objeto")
                component_id = component.get("id")
                component_type = component.get("component")
                if (
                    not isinstance(component_id, str)
                    or not COMPONENT_ID.fullmatch(component_id)
                ):
                    fail(component_location, "id de componente inválido")
                if component_id in ids_in_message:
                    fail(component_location, f"id duplicado: {component_id}")
                ids_in_message.add(component_id)
                if component_type not in surface.catalog.components:
                    fail(component_location, f"componente no permitido: {component_type!r}")
                surface.components[component_id] = component
                surface.references[component_id] = collect_references(
                    component,
                    component_location,
                )

    if message_count == 0:
        fail(str(path), "fixture vacío")
    for surface in surfaces.values():
        validate_surface(surface, str(path))


def parse_args() -> argparse.Namespace:
    skill_dir = Path(__file__).resolve().parent.parent
    default_catalogs = [
        skill_dir / "assets/starter/a2ui/catalogs/citizen-v1.catalog.json",
        skill_dir / "assets/starter/a2ui/catalogs/admin-v1.catalog.json",
    ]
    default_fixtures = [
        skill_dir / "assets/fixtures/citizen-license.valid.jsonl",
        skill_dir / "assets/fixtures/admin-operations.valid.jsonl",
    ]

    parser = argparse.ArgumentParser(
        description="Audita catálogos Nexo y streams A2UI v0.9.1.",
    )
    parser.add_argument(
        "--catalog",
        action="append",
        type=Path,
        help="Catálogo JSON. Repetir para registrar más de uno.",
    )
    parser.add_argument(
        "--fixture",
        action="append",
        type=Path,
        help="Fixture JSONL. Repetir para auditar más de uno.",
    )
    parser.add_argument(
        "--allow-url-host",
        action="append",
        default=[],
        help="Host https permitido para URLs literales.",
    )
    args = parser.parse_args()
    args.catalog = args.catalog or default_catalogs
    args.fixture = args.fixture or default_fixtures
    return args


def main() -> int:
    args = parse_args()
    allowed_hosts = {host.strip().lower() for host in args.allow_url_host if host.strip()}

    try:
        catalogs_list = [validate_catalog(path.resolve()) for path in args.catalog]
        catalogs: dict[str, Catalog] = {}
        for catalog in catalogs_list:
            if catalog.catalog_id in catalogs:
                fail(str(catalog.path), f"catalogId duplicado: {catalog.catalog_id}")
            catalogs[catalog.catalog_id] = catalog
            print(f"[OK] catálogo {catalog.catalog_id}")

        for fixture in args.fixture:
            audit_fixture(fixture.resolve(), catalogs, allowed_hosts)
            print(f"[OK] fixture {fixture}")
    except AuditError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] {len(catalogs)} catálogo(s) y {len(args.fixture)} fixture(s) auditados",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
