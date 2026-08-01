# Backend y API

## Objetivo

Exponer HTTP, SSE y webhooks, aplicar seguridad y coordinar casos de uso.

## Debe contener

FastAPI, routers `/api/v1`, autenticación, perfiles, citas, confirmaciones, healthchecks, validación y dependency injection.

## No debe contener

Prompts de dominio, SQL desde routers, render UI ni SDKs externos fuera de `integrations`.

## Convenciones

Routers delgados, casos de uso explícitos, UTC, IDs opacos, Pydantic en fronteras y errores Problem Details. Toda escritura exige permiso, consentimiento e idempotencia.

## Dependencias y mantenimiento

Puede depender de `contracts`, `orchestration`, repositorios, `integrations` y
`observability`. Los routers deben permanecer delgados y las escrituras deben
conservar permisos, consentimiento e idempotencia.

## Ejemplos y tareas

Futuros: `src/nexo_api/main.py`, `api/v1/runs.py`, `services/confirm_action.py`. Primero health/readiness, auth, conversaciones, SSE, webhooks y citas.

## Terminado

OpenAPI estable, tests de permisos/errores verdes y ningún proveedor accedido fuera de su adapter.
