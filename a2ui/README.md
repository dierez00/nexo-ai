# A2UI

## Objetivo

Transformar hechos y acciones autorizadas en superficies seguras y multicanal.

## Debe contener

Catálogos versionados, JSON Schema, builder, validator, fallbacks y fixtures A2UI v0.9.1.

## No debe contener

HTML/JavaScript generado, consultas DB, autorización ni ejecución directa de acciones.

## Convenciones

`catalogId` inmutable por versión; allowlist de componentes; datos separados de estructura; `actionId` opaco; validación servidor y cliente.

## Dependencias y responsables

Depende de `contracts`. Diego es responsable de generación/validación; Cris de renderer y accesibilidad.

## Ejemplos y tareas

`catalogs/citizen/v1`, `schemas/surface.json`, `examples/license.jsonl`. Crear catálogo MVP, fallbacks y formularios Pro.

## Terminado

Todos los fixtures válidos renderizan y cualquier componente, binding o action inválido produce fallback sin ejecución.
