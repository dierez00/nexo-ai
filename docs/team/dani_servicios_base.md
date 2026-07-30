# Dani — servicios base y backend

## 1. Objetivo general

Proporcionar una API, seguridad, canales e infraestructura local estables para que frontend y agentes evolucionen independientemente.

## 2. Responsabilidades

FastAPI, auth/RBAC, perfiles, conversaciones, runs, SSE, citas, confirmaciones, Twilio, adapters base, configuración, healthchecks, Compose, observabilidad base y CI/CD.

## 3. Carpetas bajo responsabilidad

`backend`, `integrations`, `infrastructure`, `observability` y `scripts`; custodia compartida de `contracts`.

## 4. Tareas MVP

- Bootstrap FastAPI, config y health/readiness.
- Auth, roles, perfiles y separación institucional.
- Conversaciones, mensajes, runs y SSE.
- Confirmaciones con idempotencia y citas.
- Webhooks/fallback Twilio WhatsApp Sandbox.
- Compose propuesto, logs JSONL y CI inicial.

## 5. Tareas Core

Catálogo/admin básico, webhooks robustos, perfiles completos, métricas API, pipeline events, rate limiting y documentación de arranque.

## 6. Tareas Pro

Twilio Voice, adapters reales, circuit breaker, OpenTelemetry, capa de consultas autorizadas y soporte de publicación para MCP Mapper.

## 7. Tareas Extremo

Procesos separables, salud/carga para router, retention, alertas, controles de costo y preparación de escalamiento.

## 8. Entregables concretos

OpenAPI, API/webhooks, auth, citas/actions, adapters, healthchecks, variables de entorno, imágenes/Compose, pipeline CI/CD y runbooks de despliegue/rollback.

## 9. Dependencias con otros integrantes

- Daher: migraciones, repositorios, constraints e índices.
- Diego: servicio de orquestación, eventos, MCP y model gateway.
- Cris: validación de usabilidad y cliente del contrato.

## 10. Contratos de integración

`/api/v1`, Problem Details, IDs opacos, UTC, eventos secuenciados, write con `Idempotency-Key`, webhooks firmados/deduplicados y adapters con timeout/error estable.

## 11. Riesgos y coordinación

Auth duplicada, webhooks repetidos, streaming interrumpido, pool DB, migraciones en deploy, secretos y límites Twilio. Mantener routers delgados y fixtures para fallos de proveedor.

## 12. Pruebas a implementar

API, OpenAPI, auth/RBAC, separación institucional, firmas/replay Twilio, SSE reconnect, idempotencia, timeouts, health/readiness, graceful shutdown y smoke Compose.

## 13. Criterios de aceptación

- OpenAPI sin drift.
- Permisos aplicados server-side.
- Webhook repetido no duplica mensajes/runs.
- Confirmación repetida devuelve el mismo resultado.
- Logs no contienen secretos/PII cruda.
- Fallos externos generan estados/errores explícitos.

## 14. Orden recomendado

Config → health → contratos → auth → conversaciones/runs → SSE → citas/actions → Twilio → Compose → observabilidad → CI/deploy.

## 15. Checklist

- [ ] `.env.example` sin secretos.
- [ ] CORS/CSRF/cookies/tokens.
- [ ] RBAC/tenancy.
- [ ] Request/trace IDs.
- [ ] Problem Details.
- [ ] SSE y reconexión.
- [ ] Idempotencia/confirmaciones.
- [ ] Firmas y deduplicación Twilio.
- [ ] Timeouts/retries/circuit breaker.
- [ ] Health/shutdown.
- [ ] Compose/CI/runbooks.
- [ ] README y tests.

## 16. Paralelismo y bloqueos

Puede exponer API con memoria/fixtures desde Fase 0. Persistencia final depende de Daher; SSE de schema/eventos de Diego; UI de Cris. Twilio avanza con payloads grabados. Citas requieren integrar el constraint de Daher antes de aceptación.

## Funcionalidades compartidas

| Funcionalidad | Principal | Apoyo | Contrato | Entregable | Integración |
|---|---|---|---|---|---|
| API/chat | Dani | Cris/Diego | OpenAPI/RunEvent | REST + SSE | MVP |
| Citas | Dani | Daher/Diego/Cris | Appointment/Action | Hold/confirmación | MVP |
| WhatsApp/voz | Dani | Diego | ChannelMessage | Adapters | MVP/Pro |
| Despliegue | Dani | Todos | Health/env | Compose/Railway | Cada fase |
