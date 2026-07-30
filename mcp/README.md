# MCP

## Objetivo

Publicar y ejecutar capacidades institucionales normalizadas para agentes autorizados.

## Debe contener

Server MCP, registro, schemas, tools mock/reales, seguridad, timeouts, resultados estructurados y MCP Mapper.

## No debe contener

Documentos RAG, prompts de respuesta, secretos ni ejecución arbitraria.

## Convenciones

Tool `dominio.verbo_objeto`; metadata de modo, riesgo, roles, timeout y reintentos. Toda escritura requiere confirmación, `idempotency_key` e identificador verificable.

## Dependencias y responsable

Depende de `contracts`, `integrations`, auditoría y policies de `config`. Responsable: Diego; Dani apoya adapters y red.

## Ejemplos y tareas

`tools/vehiculos.py`, `registry.py`, `mapper/openapi.py`. Crear server, tools MVP, pruebas de schema/permisos y Mapper Pro.

## Terminado

Listar/ejecutar respeta versiones y roles; no se publica una tool sin prueba/aprobación y ninguna escritura ambigua se marca exitosa.
