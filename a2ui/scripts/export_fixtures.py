"""Exporta fixtures A2UI en formato de wire para el renderer de `apps/web`.

Las superficies válidas salen del builder real (`CitizenSurfaceBuilder`) y pasan
por el validator real (`SurfaceValidator`) antes de escribirse: un fixture que el
servidor no aceptaría no sirve para probar el cliente.

Las superficies **inválidas** se escriben a mano como JSONL crudo, sin pasar por
los contratos. Es deliberado: el contrato de Pydantic rechaza en construcción
justo los payloads que el guard del cliente tiene que saber rechazar por su
cuenta, así que construirlos con el contrato sería imposible. Aquí interesa el
byte hostil tal como llegaría por el cable.

De paso mide el tramo servidor de la línea de tiempo (builder + validator) con
`perf_counter`, para que el banco de `/admin/a2ui-lab` no tenga que inventarlo.

Uso:

    uv run --python 3.12 --with-editable ./contracts --with-editable ./a2ui \\
      python a2ui/scripts/export_fixtures.py
"""

from __future__ import annotations

import json
import statistics
from datetime import UTC, date, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from nexo_a2ui import CITIZEN_CATALOG, CitizenSurfaceBuilder, SurfaceValidator
from nexo_contracts import (
    A2UI_PROTOCOL_VERSION,
    A2UIComponent,
    A2UIMessage,
    A2UISurface,
    ActionRequest,
    Channel,
    CreateSurface,
    Estimate,
    EstimateStep,
    FactCategory,
    FactValue,
    Money,
    SourceCitation,
    UpdateComponents,
    UpdateDataModel,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
# Van a `public/` para que el banco los pida por fetch: así el tramo de
# transporte se mide de verdad en vez de simularse con un import.
OUT_DIR = REPO_ROOT / "apps/web/public/fixtures/a2ui"

# Número de repeticiones para el tramo servidor. El builder es determinista y
# tarda microsegundos: con una sola corrida el ruido del reloj domina la medida.
RUNS = 200


def _citation(index: int) -> SourceCitation:
    # Los identificadores van en letras a propósito: el contrato rechaza
    # secuencias largas de dígitos porque podrían ser un teléfono o una CURP.
    suffix = "abcdefghijklmnop"[index % 16] * 12
    return SourceCitation(
        source_id=f"src_veh_{'abcd'[index % 4]}",
        fragment_id=f"frag_{suffix}",
        corpus_version="vehiculos-2026-07-30",
        source_version="v3",
        valid_from=date(2026, 1, 1),
        is_active=True,
    )


def _fact(
    fact_id: str,
    claim: str,
    category: FactCategory,
    *,
    citation_index: int = 1,
    **value: object,
) -> VerifiedFact:
    return VerifiedFact(
        fact_id=fact_id,
        claim=claim,
        value=FactValue(**value),  # type: ignore[arg-type]
        category=category,
        domain="vehiculos",
        verification=VerificationStatus.ACCEPTED,
        reason="citation_supports_claim",
        confidence=0.95,
        citations=[_citation(citation_index)],
    )


def _facts(*, requirements: int, costs: int, others: int) -> VerifiedFacts:
    """Snapshot sintético del tamaño pedido.

    El tamaño del árbol no crece con el número de hechos —el builder agrupa cada
    categoría en un solo componente— pero sí crece el data model, que es lo que
    el cliente tiene que recorrer al resolver bindings.
    """
    facts: list[VerifiedFact] = []
    for index in range(requirements):
        facts.append(
            _fact(
                f"fact_req_{index:02d}",
                f"Requisito {index + 1}: documento vigente en original y copia.",
                FactCategory.REQUIREMENT,
                citation_index=index % 4 + 1,
                items=[f"Requisito {index + 1}"],
            )
        )
    for index in range(costs):
        facts.append(
            _fact(
                f"fact_cost_{index:02d}",
                f"Concepto {index + 1}",
                FactCategory.COST,
                citation_index=index % 4 + 1,
                money=Money(amount_minor=81400 + index * 1000, currency="MXN"),
            )
        )
    for index in range(others):
        facts.append(
            _fact(
                f"fact_proc_{index:02d}",
                f"El paso {index + 1} es presencial y requiere cita previa.",
                FactCategory.PROCEDURE,
                citation_index=index % 4 + 1,
                text="presencial",
            )
        )
    return VerifiedFacts(
        snapshot_id="snapshot_cap_veh_01",
        created_at=NOW,
        facts=tuple(facts),
    )


def _action() -> ActionRequest:
    return ActionRequest(
        action_id="act_reserve_01",
        run_id="run_000001",
        tool_name="vehiculos.reservar_cita",
        input_schema_ref="contracts://tools/vehiculos.reservar_cita.input.v1",
        tool_version="1.0.0",
        expected_version=1,
        parameters={"slot_id": "slot_101"},
        required_permission="appointment:create",
    )


def _estimate() -> Estimate:
    return Estimate(
        domain="vehiculos",
        steps=[
            EstimateStep(
                step_id="renovacion",
                title="Renovación",
                cost=Money(amount_minor=81400, currency="MXN"),
                derived_from=["fact_cost_00"],
            )
        ],
        total_cost=Money(amount_minor=81400, currency="MXN"),
        derived_from=["fact_cost_00"],
    )


def _wire(surface: A2UISurface) -> str:
    """Serializa la superficie a JSONL: una unidad JSON por línea."""
    return "\n".join(message.model_dump_json_wire() for message in surface.messages) + "\n"


# --- superficie de catálogo completo ---------------------------------------


def _showcase_surface() -> A2UISurface:
    """Superficie con los 10 componentes del catálogo.

    El builder solo emite ocho: `Card` y `SlotPicker` no aparecen en los dos
    recorridos del MVP. Se arman aquí a mano —con los mismos contratos, y
    validada igual— porque el renderer sí tiene que saber dibujarlos.
    """
    surface_id = "surf_catalogo"
    action = _action()
    data = {
        "titular": "Catálogo ciudadano completo",
        "intro": "Cada componente del catálogo aparece una vez en esta superficie.",
        "requisitos": {
            "items": [
                "Identificación oficial vigente",
                "Comprobante de domicilio",
                "Certificado médico",
            ],
            "progreso": 66,
        },
        "costos": {
            "lineas": ["Renovación a tres años", "Reposición de placa"],
            "total": "1 314.00 MXN",
        },
        "detalles": [
            "El trámite es presencial y requiere cita previa.",
            "La vigencia comienza el día de la emisión.",
        ],
        "fuentes": [
            {"fuente": "src_veh_01", "version_corpus": "vehiculos-2026-07-30"},
            {"fuente": "src_veh_02", "version_corpus": "vehiculos-2026-07-30"},
        ],
        "aviso": "La licencia vence el 18 de agosto.",
        "citas": {
            "slots": ["2026-08-12 09:00", "2026-08-12 10:00", "2026-08-13 09:30"],
            "elegido": "2026-08-12 10:00",
        },
    }

    components = [
        A2UIComponent(
            id="root",
            component="Column",
            children=[
                "titular",
                "aviso",
                "resumen",
                "requisitos",
                "costos",
                "fuentes",
                "citas",
                "confirmar",
            ],
            properties={"align": "stretch", "gap": "md"},
        ),
        A2UIComponent(
            id="titular",
            component="Text",
            properties={"text": {"path": "/titular"}, "variant": "h1"},
        ),
        A2UIComponent(
            id="aviso",
            component="StatusBanner",
            properties={
                "title": "Ten en cuenta",
                "message": {"path": "/aviso"},
                "tone": "warning",
            },
        ),
        A2UIComponent(
            id="resumen",
            component="Card",
            children=["intro", "detalles"],
            properties={"title": "Resumen del trámite", "tone": "info"},
        ),
        A2UIComponent(
            id="intro",
            component="Text",
            properties={"text": {"path": "/intro"}, "variant": "body"},
        ),
        A2UIComponent(
            id="detalles",
            component="List",
            properties={"items": {"path": "/detalles"}, "ordered": False},
        ),
        A2UIComponent(
            id="requisitos",
            component="Checklist",
            properties={
                "title": "Requisitos",
                "items": {"path": "/requisitos/items"},
                "progress": {"path": "/requisitos/progreso"},
            },
        ),
        A2UIComponent(
            id="costos",
            component="CostSummary",
            properties={
                "title": "Costos",
                "lines": {"path": "/costos/lineas"},
                "total": {"path": "/costos/total"},
            },
        ),
        A2UIComponent(
            id="fuentes",
            component="SourceList",
            properties={"title": "Fuentes", "sources": {"path": "/fuentes"}},
        ),
        A2UIComponent(
            id="citas",
            component="SlotPicker",
            action_id=action.action_id,
            properties={
                "title": "Elige tu cita",
                "slots": {"path": "/citas/slots"},
                "selected": {"path": "/citas/elegido"},
            },
        ),
        A2UIComponent(
            id="confirmar",
            component="ConfirmButton",
            action_id=action.action_id,
            properties={
                "label": "Reservar cita",
                "description": "La operación se enviará una sola vez.",
            },
        ),
    ]

    return A2UISurface(
        surface_id=surface_id,
        catalog_id=CITIZEN_CATALOG.catalog_id,
        channel=Channel.WEB,
        messages=[
            A2UIMessage(
                version=A2UI_PROTOCOL_VERSION,
                create_surface=CreateSurface(
                    surface_id=surface_id,
                    catalog_id=CITIZEN_CATALOG.catalog_id,
                    send_data_model=True,
                ),
            ),
            A2UIMessage(
                version=A2UI_PROTOCOL_VERSION,
                update_data_model=UpdateDataModel(surface_id=surface_id, path="/", value=data),
            ),
            A2UIMessage(
                version=A2UI_PROTOCOL_VERSION,
                update_components=UpdateComponents(surface_id=surface_id, components=components),
            ),
        ],
        actions=[action.to_a2ui_action(label="Reservar cita")],
    )


# --- superficies hostiles ---------------------------------------------------

CATALOG_ID = "urn:nexo-ia:a2ui:catalog:citizen:v1"


def _msg(**payload: object) -> dict[str, Any]:
    return {"version": A2UI_PROTOCOL_VERSION, **payload}


def _create(surface_id: str, catalog_id: str = CATALOG_ID) -> dict[str, Any]:
    return _msg(
        createSurface={
            "surfaceId": surface_id,
            "catalogId": catalog_id,
            "sendDataModel": True,
        }
    )


def _hostile_fixtures() -> dict[str, list[dict[str, Any]]]:
    """Un caso por regla que el guard del cliente debe hacer cumplir."""
    return {
        # Catálogo que este cliente no publica: nada más debe procesarse.
        "invalid__unknown-catalog": [
            _create("surf_hostil", "urn:nexo-ia:a2ui:catalog:admin:v1"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": [], "gap": "md"}
                    ],
                }
            ),
        ],
        # `Marquee` no está en la allowlist. Registrar componentes desde el
        # payload es exactamente lo que el catálogo cerrado existe para impedir.
        "invalid__component-not-in-catalog": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {"id": "x", "component": "Marquee", "children": [], "text": "hola"},
                    ],
                }
            ),
        ],
        # `Text` admite text y variant. `onClick` ni siquiera es una propiedad:
        # es un handler intentando entrar por la puerta de las props.
        "invalid__unknown-property": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "Text",
                            "children": [],
                            "text": "hola",
                            "onClick": "fetch('https://evil.example')",
                        },
                    ],
                }
            ),
        ],
        # HTML crudo en una propiedad de texto.
        "invalid__html-injection": [
            _create("surf_hostil"),
            _msg(
                updateDataModel={
                    "surfaceId": "surf_hostil",
                    "path": "/",
                    "value": {"titular": "<script>fetch('https://evil.example')</script>"},
                }
            ),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "Text",
                            "children": [],
                            "text": {"path": "/titular"},
                            "dangerouslySetInnerHTML": {"__html": "<img onerror=alert(1)>"},
                        },
                    ],
                }
            ),
        ],
        # Un binding que no resuelve no es fatal (queda en loading), pero un
        # puntero que no es JSON Pointer absoluto sí es payload malformado.
        "invalid__broken-binding": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "Text",
                            "children": [],
                            "text": {"path": "../../etc/passwd"},
                        },
                    ],
                }
            ),
        ],
        # Un `Text` con acción sería un botón invisible.
        "invalid__action-on-non-interactive": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "Text",
                            "children": [],
                            "text": "inocente",
                            "actionId": "act_reserve_01",
                        },
                    ],
                }
            ),
        ],
        # La acción no está declarada en la superficie: nadie la autorizó.
        "invalid__action-not-declared": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "ConfirmButton",
                            "children": [],
                            "label": "Confirmar",
                            "actionId": "act_de_otro_run",
                        },
                    ],
                }
            ),
        ],
        # Propiedad que no es un handler ni marcado: simplemente no está
        # declarada para `Checklist`. Aísla la regla de allowlist de propiedades,
        # que los casos anteriores tapan al disparar reglas más agresivas.
        "invalid__property-off-allowlist": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "Checklist",
                            "children": [],
                            "title": "Requisitos",
                            "items": [],
                            "variant": "compacta",
                        },
                    ],
                }
            ),
        ],
        # `data:` no contiene la palabra javascript ni marcado, así que llega
        # hasta la política de esquemas de URL. Es el caso que la aísla.
        "invalid__url-scheme-not-allowed": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "SourceList",
                            "children": [],
                            "title": "Fuentes",
                            "sources": [
                                {
                                    "fuente": "src_01",
                                    "version_corpus": "v1",
                                    "url": "data:text/html;base64,PGltZz4=",
                                }
                            ],
                        },
                    ],
                }
            ),
        ],
        # Esquemas de URL que son vectores de ejecución dentro del renderer.
        "invalid__unsafe-url": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {
                            "id": "x",
                            "component": "SourceList",
                            "children": [],
                            "title": "Fuentes",
                            "sources": [
                                {
                                    "fuente": "src_01",
                                    "version_corpus": "v1",
                                    "url": "javascript:alert(1)",
                                }
                            ],
                        },
                    ],
                }
            ),
        ],
        # Sin `createSurface` no hay superficie a la que aplicar nada.
        "invalid__missing-create-surface": [
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": [], "gap": "md"}
                    ],
                }
            ),
        ],
        # Un árbol sin `root` no tiene por dónde empezar a dibujarse.
        "invalid__without-root": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "titulo", "component": "Text", "children": [], "text": "hola"}
                    ],
                }
            ),
        ],
        # Dos componentes con el mismo id: el árbol deja de ser resoluble.
        "invalid__duplicate-ids": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {"id": "x", "component": "Text", "children": [], "text": "uno"},
                        {"id": "x", "component": "Text", "children": [], "text": "dos"},
                    ],
                }
            ),
        ],
        # `Text` no admite hijos; permitirlo abriría recursión no prevista.
        "invalid__children-not-allowed": [
            _create("surf_hostil"),
            _msg(
                updateComponents={
                    "surfaceId": "surf_hostil",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["x"], "gap": "md"},
                        {"id": "x", "component": "Text", "children": ["y"], "text": "hola"},
                        {"id": "y", "component": "Text", "children": [], "text": "hijo"},
                    ],
                }
            ),
        ],
        # Versión de protocolo distinta de la que Nexo fija.
        "invalid__wrong-version": [
            {
                "version": "v0.8.0",
                "createSurface": {
                    "surfaceId": "surf_hostil",
                    "catalogId": CATALOG_ID,
                    "sendDataModel": True,
                },
            },
        ],
    }


# --- medición del tramo servidor -------------------------------------------


def _measure(facts: VerifiedFacts, validator: SurfaceValidator) -> dict[str, float]:
    builder = CitizenSurfaceBuilder()
    action = _action()
    run_actions = frozenset({action.action_id})

    build_ms: list[float] = []
    validate_ms: list[float] = []

    for _ in range(RUNS):
        start = perf_counter()
        surface = builder.build(
            facts,
            surface_id="surf_bench",
            estimate=_estimate(),
            pending_action=action,
        )
        middle = perf_counter()
        validator.validate(surface, run_action_ids=run_actions)
        end = perf_counter()
        build_ms.append((middle - start) * 1000)
        validate_ms.append((end - middle) * 1000)

    def _p(values: list[float], q: float) -> float:
        ordered = sorted(values)
        index = min(int(q * len(ordered)), len(ordered) - 1)
        return round(ordered[index], 4)

    return {
        "runs": RUNS,
        "build_p50_ms": _p(build_ms, 0.50),
        "build_p95_ms": _p(build_ms, 0.95),
        "validate_p50_ms": _p(validate_ms, 0.50),
        "validate_p95_ms": _p(validate_ms, 0.95),
        "total_p50_ms": round(statistics.median(build_ms) + statistics.median(validate_ms), 4),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    builder = CitizenSurfaceBuilder()
    validator = SurfaceValidator(catalog=CITIZEN_CATALOG)
    action = _action()
    run_actions = frozenset({action.action_id})

    manifest: list[dict[str, Any]] = []

    # Superficies válidas de tres tamaños. El tamaño que le importa al cliente
    # es el del data model, no el del árbol.
    sizes = {
        "valid__small": _facts(requirements=2, costs=1, others=1),
        "valid__medium": _facts(requirements=10, costs=6, others=9),
        "valid__large": _facts(requirements=40, costs=25, others=35),
    }

    for name, facts in sizes.items():
        surface = builder.build(
            facts,
            surface_id="surf_licencia",
            estimate=_estimate(),
            pending_action=action,
            headline="Renovación de licencia de conducir",
            warnings=("Tu licencia vence el 18 de agosto.",),
        )
        result = validator.validate(surface, run_action_ids=run_actions)
        if not result.is_valid:
            raise SystemExit(f"{name}: el builder produjo una superficie inválida: {result}")

        wire = _wire(surface)
        (OUT_DIR / f"{name}.jsonl").write_text(wire, encoding="utf-8")
        components = sum(
            len(m.update_components.components)
            for m in surface.messages
            if m.update_components is not None
        )
        manifest.append(
            {
                "name": name,
                "valid": True,
                "components": components,
                "facts": len(facts.facts),
                "bytes": len(wire.encode("utf-8")),
            }
        )

    # Catálogo completo: los 10 componentes en una sola superficie.
    showcase = _showcase_surface()
    result = validator.validate(showcase, run_action_ids=run_actions)
    if not result.is_valid:
        raise SystemExit(f"la superficie de catálogo no valida: {result}")
    wire = _wire(showcase)
    (OUT_DIR / "valid__catalog.jsonl").write_text(wire, encoding="utf-8")
    manifest.append(
        {
            "name": "valid__catalog",
            "valid": True,
            "components": 11,
            "facts": 0,
            "bytes": len(wire.encode("utf-8")),
        }
    )

    # Superficies hostiles.
    for name, messages in _hostile_fixtures().items():
        wire = "\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n"
        (OUT_DIR / f"{name}.jsonl").write_text(wire, encoding="utf-8")
        manifest.append(
            {
                "name": name,
                "valid": False,
                "rule": name.split("__", 1)[1],
                "bytes": len(wire.encode("utf-8")),
            }
        )

    timings = {
        "generated_at": datetime.now(UTC).isoformat(),
        "note": (
            "Tramo servidor de la línea de tiempo: builder determinista + validator. "
            "No incluye el modelo (produce VerifiedFacts aguas arriba) ni el transporte."
        ),
        "by_size": {name: _measure(facts, validator) for name, facts in sizes.items()},
    }
    (OUT_DIR / "timings.json").write_text(
        json.dumps(timings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    valid = sum(1 for item in manifest if item["valid"])
    print(f"{len(manifest)} fixtures en {OUT_DIR.relative_to(REPO_ROOT)}")
    print(f"  {valid} válidos, {len(manifest) - valid} hostiles")
    for name, measure in timings["by_size"].items():
        print(
            f"  {name}: build p50 {measure['build_p50_ms']} ms · "
            f"validate p50 {measure['validate_p50_ms']} ms"
        )


if __name__ == "__main__":
    main()
