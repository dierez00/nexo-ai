# Dani — servicios base y backend

## 1. Objetivo general

Proporcionar una API, seguridad, canales e infraestructura local estables para que frontend y agentes evolucionen independientemente.

## 2. Responsabilidades

FastAPI, auth/RBAC, perfiles, conversaciones, runs, SSE, citas, confirmaciones, Twilio, adapters base, configuración, healthchecks, Compose, observabilidad base y CI/CD.

## 3. Carpetas bajo responsabilidad

`backend`, `integrations`, `infrastructure`, `observability` y `scripts`; custodia compartida de `contracts`.

## 4. Tareas MVP

- [x] Bootstrap FastAPI, config y health/readiness.
- [x] Auth, roles, perfiles y separación institucional. *(Supabase Auth+JWKS; tenancy por tenant_id en repos)*
- [x] Conversaciones, mensajes, runs y SSE. *(SSE reanudable por Last-Event-ID; auth por header o query param)*
- [x] Confirmaciones con idempotencia y citas. *(citas: availability + holds; solapamiento→409 vía GiST)*
- [x] Webhooks/fallback Twilio WhatsApp Sandbox. *(firma verificada, dedupe por provider_message_id, TwiML)*
- [x] Compose propuesto, logs JSONL y CI inicial. *(Dockerfile + docker-compose + GitHub Actions lint/test)*

## 5. Tareas Core

- [x] Catálogo/admin básico. *(`GET /api/v1/admin/catalog` operativo por tenant + `GET /admin/config` con la config canónica vía loader de `nexo_orchestration`)*
- [x] Webhooks robustos. *(fallback 2xx ante fallo de orquestación; tracking de entrega por `MessageSid` + log estructurado)*
- [x] Perfiles completos. *(lectura enriquecida: institution/branch/is_owner/preferences. PATCH de preferencias queda **fuera de alcance**)*
- [x] Métricas API. *(`GET /api/v1/admin/metrics` → `MetricSet` tenant-scoped por ventana; rol admin)*
- [x] Pipeline events. *(`GET /runs/{id}/events/list` replay + emisión JSONL; `RunEvent` canónico con `correlation_id`)*
- [x] Rate limiting. *(token bucket in-app por tenant/usuario → 429 RATE_LIMITED en escrituras. **Limitación**: estado no compartido entre réplicas; multi-réplica requeriría estado compartido, fuera de alcance)*
- [x] Documentación de arranque. *(`scripts/run.{sh,ps1}` de una línea + runbook en `docs/runbooks/arranque.md`)*

Admin gated por `require_role("admin")`. Contratos canónicos (`nexo_contracts`) adoptados; OpenAPI regenerado sin drift.

## Estado operativo actualizado (2026-07-30)

- El workspace `uv` incluye los ocho paquetes Python y CI valida lockfile, lint,
  tipos y pruebas. Las pruebas con Supabase local para concurrencia quedan como
  gate de integración al habilitar ese entorno en CI.
- Todas las escrituras HTTP actuales usan el ledger compartido de idempotencia:
  confirmaciones y holds reservan la clave antes del efecto, validan hash de
  request y conservan `unknown` sin reintento automático.
- Los runs responden `202` y se ejecutan en una tarea administrada por la API.
  SSE hace polling de eventos persistidos por `sequence`, reanuda con
  `Last-Event-ID` y termina tras el estado terminal. Es una garantía MVP en
  proceso: reiniciar la API cancela trabajo activo.
- Dependencias: Daher aprueba/aplica la migración de ledger y secuencias; Diego
  conecta el `EventSinkPort` del grafo real al adaptador de persistencia; Cris
  consume la secuencia SSE y el estado `queued`.

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

- [x] `.env.example` sin secretos.
- [x] CORS/CSRF/cookies/tokens. *(CORS + JWT bearer; CSRF n/a con bearer)*
- [x] RBAC/tenancy. *(require_permission + filtrado tenant_id)*
- [x] Request/trace IDs. *(TraceIdMiddleware, header X-Trace-Id)*
- [x] Problem Details.
- [x] SSE y reconexión. *(sse-starlette; Last-Event-ID; token por query param para EventSource)*
- [x] Idempotencia/confirmaciones. *(Idempotency-Key + replay idéntico; consent→422; RBAC por módulo)*
- [x] Firmas y deduplicación Twilio. *(RequestValidator; pii_ref del remitente; dedupe idempotente)*
- [ ] Timeouts/retries/circuit breaker. *(Pro)*
- [x] Health/shutdown.
- [x] Compose/CI/runbooks. *(runbook en docs/runbooks/arranque.md: local, Docker, Twilio, deploy/rollback, troubleshooting)*
- [x] README y tests. *(33 tests verdes; OpenAPI autogenerado en /docs; READMEs por módulo)*

## 16. Paralelismo y bloqueos

Puede exponer API con memoria/fixtures desde Fase 0. Persistencia final depende de Daher; SSE de schema/eventos de Diego; UI de Cris. Twilio avanza con payloads grabados. Citas requieren integrar el constraint de Daher antes de aceptación.

## Funcionalidades compartidas

| Funcionalidad | Principal | Apoyo | Contrato | Entregable | Integración |
|---|---|---|---|---|---|
| API/chat | Dani | Cris/Diego | OpenAPI/RunEvent | REST + SSE | MVP |
| Citas | Dani | Daher/Diego/Cris | Appointment/Action | Hold/confirmación | MVP |
| WhatsApp/voz | Dani | Diego | ChannelMessage | Adapters | MVP/Pro |
| Despliegue | Dani | Todos | Health/env | Compose/Railway | Cada fase |
