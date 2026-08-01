# Servicios de plataforma

La plataforma expone API, autenticación, conversaciones, runs, SSE, acciones,
citas, voz, webhooks, healthchecks, rate limiting y Problem Details.

## Prioridades

- Mantener el contrato OpenAPI alineado con `contracts`.
- Persistir eventos y checkpoints sin perder orden ni visibilidad.
- Ejecutar escrituras con permiso, confirmación e idempotencia.
- Separar los runs activos en un worker durable.
- Cubrir integración, recuperación y observabilidad con pruebas automatizadas.
