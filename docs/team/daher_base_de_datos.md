# Daher — base de datos

## 1. Objetivo general

Garantizar un modelo consistente, seguro y reproducible para operación, RAG, citas, trazas, auditoría y analítica.

## 2. Responsabilidades

ERD, PostgreSQL/pgvector, Alembic, repositorios, constraints, índices, seeds, consultas, tenancy, retención, backup/restore y rendimiento.

## 3. Carpetas bajo responsabilidad

`database`; apoyo en `data`, `tests/integration`, `observability/dashboards` y contratos de persistencia.

## 4. Tareas MVP

- Instituciones, users/profiles/RBAC.
- Conversations/messages/runs/events.
- Sources/documents/chunks/pgvector.
- Tool registry/calls.
- Appointments/holds y constraint GiST.
- Actions, idempotency y audit log.
- Seeds de vehículos/empresas.

## 5. Tareas Core

Catálogo completo, cinco namespaces, métricas, búsqueda híbrida, retención e índices.

## 6. Tareas Pro

Integrations/tool versions, voz, folios reales, consultas analíticas permitidas y runbook backup/restore.

## 7. Tareas Extremo

Judge results, prompts versionados, contradicciones, corpus versions, optimización/particionamiento y aislamiento institucional avanzado.

## 8. Entregables concretos

ERD, diccionario, migraciones, constraints, repositorios, seeds idempotentes, queries aprobadas, índices/EXPLAIN, backup plan y pruebas concurrentes.

## 9. Dependencias con otros integrantes

- Dani: casos de uso y transacciones API.
- Diego: metadata RAG, RunEvent, tool/judge contracts.
- Cris: métricas/filtros visibles.

## 10. Contratos de integración

IDs opacos, `institution_id`, `timestamptz`, money minor units, vector dimension configurada, soft/delete-retention cuando aplique, eventos/auditoría append-only y repositorios como frontera.

## 11. Riesgos y coordinación

Schema cambiante, dimensión de embeddings, locks GiST, PII en auditoría, queries caras y migraciones irreversibles. Congelar entidades MVP y revisar cualquier cambio de contrato.

## 12. Pruebas a implementar

Migración vacía/upgrade, seeds repetidos, FK/check/unique/exclude, reservas concurrentes, tenancy, vigencia RAG, índices/EXPLAIN, idempotencia y backup smoke.

## 13. Criterios de aceptación

- Cero citas solapadas persisted.
- Migraciones reproducibles.
- RAG filtra dominio/institución/vigencia.
- Seeds no duplican.
- Auditoría conserva actor/acción/resultado sin secretos.
- Queries críticas usan índices apropiados.

## 14. Orden recomendado

Glosario/ERD → extensiones → identidad → catálogo/RAG → runs/events → citas/actions → auditoría → seeds → índices/analítica → backup.

## 15. Checklist

- [x] PK/FK y ownership.
- [x] Unique/check/exclude.
- [x] Índices y query plans.
- [x] UTC/money/IDs.
- [x] Tenancy y permisos.
- [x] Retención/masking.
- [x] Migraciones expand/contract.
- [x] Seeds idempotentes.
- [x] Backup/restore.
- [x] Diccionario/ERD.
- [x] Tests concurrentes.

## 16. Paralelismo y bloqueos

ERD, extensiones y fixtures avanzan desde Fase 0. Los campos definitivos dependen de contratos de Dani/Diego; dashboards esperan necesidades de Cris; optimización espera datos de carga. API/agentes usan repositorios fake mientras llegan migraciones.

## Funcionalidades compartidas

| Funcionalidad | Principal | Apoyo | Contrato | Entregable | Integración |
|---|---|---|---|---|---|
| Citas/holds | Daher (integridad) | Dani | Appointment | Constraint + caso de uso | MVP |
| RAG store | Daher (schema) | Diego | Source/Chunk | Migración + retriever | MVP |
| Auditoría | Daher | Dani/Diego | RunEvent/Audit | Tablas + append | MVP |
| Dashboard | Cris | Daher | MetricSet | Queries/indexes | Core |
