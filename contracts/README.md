# Contratos

## Objetivo

Mantener las interfaces que permiten trabajar en paralelo sin compartir implementaciones.

## Debe contener

OpenAPI, JSON Schema, estados, eventos, ejemplos, changelog y reglas de compatibilidad.

## No debe contener

Lógica de negocio, secretos, tipos duplicados manualmente ni fixtures incompatibles.

## Convenciones

Wire format `snake_case`, UTC, IDs opacos, montos en minor units y cambios incompatibles mediante versión nueva. Pydantic/OpenAPI será la fuente del cliente TypeScript generado.

## Dependencias y mantenimiento

No depende de lógica de negocio. Los cambios incompatibles requieren nueva
versión, artefactos derivados actualizados y pruebas de consumidores.

## Ejemplos y tareas

`openapi/v1.yaml`, `jsonschema/verified_facts.json`, `events/run.schema.json`. Congelar MVP, generar cliente y ejecutar contract tests.

## Terminado

Frontend, API, agentes, MCP y A2UI aceptan los mismos fixtures sin traducciones implícitas.

## Estado tras Fase 0

Los modelos Pydantic de `src/nexo_contracts/` son la **fuente de verdad**. Todo
lo demás se genera con `python -m nexo_contracts.export` y no se edita a mano:

- `jsonschema/` y `events/` — 56 JSON Schema más `index.json`.
- `examples/valid/` — un ejemplo canónico por contrato.
- `examples/invalid/` — 26 payloads que deben rechazarse, con la regla que los
  detecta en `manifest.json`.
- `domains/*/fixtures/` — fixtures de los dos recorridos MVP.

Compatibilidad y proceso de aprobación: [`CHANGELOG.md`](./CHANGELOG.md).
Convenciones transversales: [`docs/architecture/conventions.md`](../docs/architecture/conventions.md).

Un contract test falla si un artefacto publicado se desincroniza del modelo.
