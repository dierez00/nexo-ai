# Contratos

## Objetivo

Mantener las interfaces que permiten trabajar en paralelo sin compartir implementaciones.

## Debe contener

OpenAPI, JSON Schema, estados, eventos, ejemplos, changelog y reglas de compatibilidad.

## No debe contener

Lógica de negocio, secretos, tipos duplicados manualmente ni fixtures incompatibles.

## Convenciones

Wire format `snake_case`, UTC, IDs opacos, montos en minor units y cambios incompatibles mediante versión nueva. Pydantic/OpenAPI será la fuente del cliente TypeScript generado.

## Dependencias y responsables

No depende de lógica. Dani custodia; Cris, Daher y Diego aprueban sus fronteras.

## Ejemplos y tareas

`openapi/v1.yaml`, `jsonschema/verified_facts.json`, `events/run.schema.json`. Congelar MVP, generar cliente y ejecutar contract tests.

## Terminado

Frontend, API, agentes, MCP y A2UI aceptan los mismos fixtures sin traducciones implícitas.
