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
    export_catalog,
    load_catalog,
    render_catalog_json,
)
from .fallback import build_fallback
from .validator import ALLOWED_URL_SCHEMES, SurfaceValidator

__all__ = [
    "ALLOWED_PROPERTIES",
    "ALLOWED_TONES",
    "ALLOWED_URL_SCHEMES",
    "CITIZEN_CATALOG",
    "CITIZEN_CATALOG_ID",
    "CITIZEN_CATALOG_PATH",
    "CitizenSurfaceBuilder",
    "SurfaceValidator",
    "build_fallback",
    "export_catalog",
    "format_money",
    "load_catalog",
    "render_catalog_json",
]
