"""Generación y validación de superficies A2UI v0.9.1 en servidor (Fase 1).

Este paquete construye superficies desde plantillas y hechos verificados, las
valida contra un catálogo cerrado y produce un fallback textual cuando la
validación falla. Nada de lo que produce se ejecuta: HTML, JavaScript, SQL o
código generado por un modelo no tienen representación posible en estos
contratos (ADR 0006).

No consulta tablas, no autoriza acciones y no decide el plan del run: recibe
`VerifiedFacts` y acciones ya autorizadas, y devuelve estructura.
"""

from .builder import CitizenSurfaceBuilder, format_money
from .catalog import (
    ALLOWED_PROPERTIES,
    ALLOWED_TONES,
    CITIZEN_CATALOG,
    CITIZEN_CATALOG_ID,
    CITIZEN_CATALOG_PATH,
    CITIZEN_FREEZE_PATH,
    FrozenCatalogManifest,
    export_catalog,
    load_catalog,
    load_freeze_manifest,
    render_catalog_json,
    verify_frozen_catalog,
)
from .fallback import build_fallback
from .fixtures import load_jsonl, parse_jsonl, render_jsonl, surface_from_messages
from .validator import ALLOWED_URL_SCHEMES, SurfaceValidator

__all__ = [
    "ALLOWED_PROPERTIES",
    "ALLOWED_TONES",
    "ALLOWED_URL_SCHEMES",
    "CITIZEN_CATALOG",
    "CITIZEN_CATALOG_ID",
    "CITIZEN_CATALOG_PATH",
    "CITIZEN_FREEZE_PATH",
    "CitizenSurfaceBuilder",
    "FrozenCatalogManifest",
    "SurfaceValidator",
    "build_fallback",
    "load_jsonl",
    "parse_jsonl",
    "render_jsonl",
    "surface_from_messages",
    "export_catalog",
    "format_money",
    "load_freeze_manifest",
    "load_catalog",
    "render_catalog_json",
    "verify_frozen_catalog",
]
