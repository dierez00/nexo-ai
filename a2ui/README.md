# A2UI

## Objetivo

Transformar hechos y acciones autorizadas en superficies seguras y multicanal.

## Debe contener

Catálogos versionados, JSON Schema, builder, validator, fallbacks y fixtures A2UI v0.9.1.

## No debe contener

HTML/JavaScript generado, consultas DB, autorización ni ejecución directa de acciones.

## Convenciones

`catalogId` inmutable por versión; allowlist de componentes; datos separados de estructura; `actionId` opaco; validación servidor y cliente.

## Dependencias y mantenimiento

Depende de `contracts`. El renderer y su contrato citizen v1 se consideran
cerrados; el flujo debe conservar la compatibilidad del catálogo y sus fixtures.

## Ejemplos y tareas

`catalogs/citizen/v1`, `schemas/surface.json`, `examples/license.jsonl`. Crear catálogo MVP, fallbacks y formularios Pro.

## Terminado

Todos los fixtures válidos renderizan y cualquier componente, binding o action inválido produce fallback sin ejecución.

## Estado tras Fase 1

El catálogo citizen v1, builder, validator y fallbacks están implementados. Los
streams de `fixtures/citizen/v1/` contienen dos casos válidos y tres
adversariales en JSONL A2UI v0.9.1; pruebas compartidas verifican componentes,
propiedades, bindings, URLs y pertenencia de acciones al run.

El catálogo `urn:nexo-ia:a2ui:catalog:citizen:v1` está **congelado**. Su
manifiesto, huellas y regla de versionado están en
[`catalogs/citizen/v1/FROZEN.md`](./catalogs/citizen/v1/FROZEN.md). Cambiar
componentes, propiedades, schemas o fixtures requiere publicar `citizen:v2`;
el trabajo pendiente es conectar `RunResult.surface.messages` al transporte y
renderer existentes.
