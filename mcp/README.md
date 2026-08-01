# MCP

## Objetivo

Publicar y ejecutar capacidades institucionales normalizadas para agentes autorizados.

## Debe contener

Server MCP, registro, schemas, tools mock/reales, seguridad, timeouts, resultados estructurados y MCP Mapper.

## No debe contener

Documentos RAG, prompts de respuesta, secretos ni ejecución arbitraria.

## Convenciones

Tool `dominio.verbo_objeto`; metadata de modo, riesgo, roles, timeout y reintentos. Toda escritura requiere confirmación, `idempotency_key` e identificador verificable.

## Dependencias y mantenimiento

Depende de `contracts`, `integrations`, auditoría y policies de `config`. Toda
tool debe declarar schema, permisos, timeout, idempotencia y resultado auditable.

## Ejemplos y tareas

`tools/vehiculos.py`, `registry.py`, `mapper/openapi.py`. Crear server, tools MVP, pruebas de schema/permisos y Mapper Pro.

## Terminado

Listar/ejecutar respeta versiones y roles; no se publica una tool sin prueba/aprobación y ninguna escritura ambigua se marca exitosa.

## Estado tras Fase 1

Solo puertos y dobles: `ToolRegistryPort` y `ToolExecutorPort` en `ports.py`,
con implementaciones en memoria en `testing/`.

El executor reproduce los cinco desenlaces que el sistema debe saber manejar
—éxito, timeout, error de schema, permiso denegado y outcome desconocido— y
revalida la autorización por su cuenta aunque el supervisor ya haya filtrado.

Implementados server MCP, catálogo versionado, autorización independiente,
executor y nueve tools mock de los dos dominios MVP. Las escrituras exigen
consentimiento, permiso, idempotencia y folio verificable; los parámetros y
eventos de auditoría se minimizan.

El MCP Mapper permanece fuera de alcance hasta Fase 3 (F3.2).

Aislamiento de escrituras: [ADR 0005](../docs/adr/0005-mcp-frontera-de-capacidades.md).
