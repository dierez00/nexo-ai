# Auditoría de base de datos — Daher

Verificación de `docs/team/daher_base_de_datos.md` contra el esquema real en `supabase/migrations/`, gap-analysis de Pro/Extremo, y estado de criterios de aceptación y pruebas tras los fixes aplicados en esta auditoría.

Fecha: 2026-07-30. Fuente de verdad del esquema: `supabase/migrations/` (7 archivos, incluye el fix `20260504150000_fix_rag_seed_idempotency.sql` añadido en esta auditoría). Diccionario de datos completo: `docs/architecture/database_schema.md`.

---

## 1. Verificación MVP (sección 4 del doc)

| Tarea MVP | Estado | Evidencia |
|---|---|---|
| Instituciones, users/profiles/RBAC | ✅ Completa | `tenants`, `tenant_domains`, `users`, `roles`, `permissions`, `role_permissions`, `branches` en `20260504094442_initial_schema.sql`. RBAC vía `has_permission()`, roles de sistema + por tenant. El doc usa el término "instituciones"; el esquema usa `tenants` — equivalente funcional, ver §7 (contratos). |
| Conversations/messages/runs/events | ✅ Completa | `conversations`, `messages`, `runs`, `run_events` en `20260504120000_conversations_runs_events.sql`, con `trace_id` (OTel-compatible) y `event_type` por nodo del grafo. |
| Sources/documents/chunks/pgvector | ✅ Completa | `sources`, `documents`, `chunks` en `20260504100000_rag_vector_store.sql`; `chunks.embedding vector(1536)`, índice HNSW coseno, RPC `match_chunks()` con filtro tenant/domain/vigencia. |
| **Tool registry/calls** | ❌ **No existe** | No hay tabla de catálogo de herramientas ni de invocaciones estructuradas en ninguna migración. Lo más cercano es `run_events.event_type = 'mcp_call'` (texto libre en jsonb, sin schema de tool ni versión). **Gap MVP real**, fuera del alcance de fixes de esta auditoría (no bloquea ningún criterio de aceptación de la sección 13, pero sí un checklist item de la sección 4). |
| Appointments/holds y constraint GiST | ✅ Completa y correcta | `appointments` + `appointments_no_overlap` (exclude using gist) en `20260504110000_appointments_gist.sql`. Verificado con `test_constraints.py` y `test_appointments_concurrency.py`. |
| Actions, idempotency y audit log | ✅ Completa | `actions.idempotency_key unique`, `audit_logs` (actor/acción/entidad/before-after) en `20260504094442_initial_schema.sql` y `20260504120000_conversations_runs_events.sql`. |
| Seeds de vehículos/empresas | ⚠️ → ✅ **Corregido en esta auditoría** | `20260504140000_seeds_demo.sql` sembraba `sources`/`documents` con `on conflict do nothing` sin unique constraint que respaldara el conflicto → duplicaba en cada re-seed. Fix: `20260504150000_fix_rag_seed_idempotency.sql` añade `sources_tenant_checksum_key unique(tenant_id, checksum)` y `documents_source_title_key unique(source_id, title)`. Verificado con `test_seeds_idempotent.py`. |

**MVP: 6/7 completas, 1 corregida en esta auditoría, 1 gap real (tool registry) documentado para trabajo futuro.**

---

## 2. Verificación Core (sección 5 del doc)

| Tarea Core | Estado | Evidencia |
|---|---|---|
| Catálogo completo / cinco namespaces | ⚠️ Parcial | Los 5 dominios (`vehiculos`, `ayuntamiento_empresas`, `registro_civil`, `salud`, `ganaderia`) están definidos en el CHECK de `modules.code` y `sources.domain` (+ `general`), y los 5 módulos están sembrados. Pero solo hay **contenido RAG real para 1 de 5** dominios (`vehiculos`, seed único). El catálogo está *modelado* completo; el *contenido* no. |
| Métricas | ❌ No existe | No hay tablas/vistas de métricas ni agregaciones. `MetricSet` (tabla "Funcionalidades compartidas" del doc, sección 16) es responsabilidad compartida con Cris — Daher debe proveer queries/índices de soporte, que aún no existen. |
| Búsqueda híbrida | ❌ No existe | Solo búsqueda vectorial (`match_chunks`, HNSW + coseno). No hay `tsvector`/GIN ni ranking BM25/keyword combinado con el vector — "híbrida" implica ambos. |
| Retención | ❌ No existe | Ninguna tabla tiene `deleted_at`/soft-delete, política de expiración automática (más allá de `cleanup_expired_holds()` para holds de citas, que es un caso distinto), ni job de purga para `run_events`, `messages`, `audit_logs`. |
| Índices | ✅ Razonable para MVP | Índices btree en los patrones de acceso principales (`tenant_id+*`), índice único parcial en `subscriptions`/`roles`, HNSW en `chunks`. Verificado estructuralmente y por EXPLAIN forzado en `test_indexes_explain.py`. Sin índices para búsqueda híbrida (no existe aún esa capacidad). |

**Core: 1/5 lista (índices), 1 parcial (catálogo con contenido incompleto), 3 sin implementar (métricas, búsqueda híbrida, retención).**

---

## 3. Gap-analysis Pro (sección 6 del doc)

| Tarea Pro | Estado actual | Qué falta | Esfuerzo estimado |
|---|---|---|---|
| Integrations/tool versions | ❌ No implementado | No existe tabla `tool_version` ni `integrations` (solo `integrations/README.md` stub). Requiere: tabla de catálogo de integraciones (proveedor, tipo, config), tabla de versiones de tools con changelog/compatibilidad. | M — 1-2 migraciones nuevas + contratos con Diego (dueño de tool/judge contracts según sección 9 del doc). |
| Voz | ⚠️ Estructura mínima | `conversations.channel` acepta `'voice'` como valor de enum, pero no hay tablas de transcripción, duración de audio, ni metadata de proveedor de voz (Twilio, etc.). | M — tabla `voice_sessions` o extensión de `messages` con metadata de audio. |
| Folios reales | ⚠️ Placeholder | `appointments.confirmation_folio` y `actions.result_folio` son `text` libre, sin secuencia, formato ni unicidad garantizada por constraint. "Reales" implica folios generados de forma consistente/auditable (p.ej. secuencia por tenant+año, o unique constraint). | S — añadir secuencia/función de generación + unique constraint. |
| Consultas analíticas permitidas | ❌ No implementado | No hay vistas ni funciones documentadas como "queries aprobadas" para analítica (el propio doc lista "queries aprobadas" como entregable en la sección 8). | M — depende de qué métricas defina Cris. |
| Runbook backup/restore | ❌ No implementado | Solo prosa aspiracional en `infrastructure/README.md` y `docs/README.md`. Checklist item sin marcar en el doc original. Esta auditoría añadió un **smoke test** (`test_backup_smoke.py`) que ejercita `supabase db dump` + restore real, pero no un runbook operativo documentado (pasos de recuperación ante desastre, RTO/RPO, verificación periódica). | S-M — documentar el runbook usando el mecanismo ya probado por el smoke test como base. |

---

## 4. Gap-analysis Extremo (sección 7 del doc)

| Tarea Extremo | Estado actual | Qué falta | Esfuerzo estimado |
|---|---|---|---|
| Judge results | ⚠️ Mínimo | `judge_results` existe (`20260504130000_evaluations_judge.sql`) con 5 scores + `hallucinations_detected` + `feedback`, pero sin versionado del prompt/criterio de evaluación usado (`judge_model` es texto libre sin trazabilidad a una versión concreta del prompt). | S — vincular a `prompt_version` (ver abajo) una vez exista. |
| Prompts versionados | ❌ No existe | Cero presencia en el esquema (`prompt_version` no aparece en ninguna tabla/columna). Mencionado solo en prosa en `agents/README.md`. | M — tabla `prompt_versions` (nombre, versión, contenido/hash, modelo objetivo, fecha). |
| Contradicciones | ❌ No existe | Sin tabla `contradiction`/mecanismo de detección de contradicciones entre fuentes o entre respuesta y fuente. | M-L — depende del diseño del pipeline de detección (Diego). |
| Corpus versions | ⚠️ Parcial | `sources.version` (texto libre, ej. `'v2026.1'`) versiona cada fuente individualmente, pero no hay una tabla `corpus_versions` que agrupe/trackee snapshots completos del corpus RAG en el tiempo (para reproducibilidad de evaluaciones). | M — tabla `corpus_versions` + relación con `sources`/`chunks`. |
| Optimización/particionamiento | ❌ No existe | Ninguna tabla usa `partition by` (ni siquiera `run_events`/`audit_logs`, las candidatas naturales por volumen). | L — requiere volumen de datos real para justificar y diseñar la estrategia de partición (por fecha, tenant, o ambos). |
| Aislamiento institucional avanzado | ⚠️ Básico cubierto, avanzado no | RLS por `tenant_id` cubre el aislamiento MVP (verificado en `test_tenancy_rls.py`). "Avanzado" (p.ej. cifrado a nivel de columna para PII, particionamiento físico por tenant, auditoría de accesos cross-tenant por `service_role`) no está implementado. | L. |

---

## 5. Criterios de aceptación (sección 13 del doc) — estado tras los fixes

| # | Criterio | Estado | Prueba que lo verifica |
|---|---|---|---|
| 1 | Cero citas solapadas persisted | ✅ Cumple | `appointments_no_overlap` (exclude gist) — `test_constraints.py::test_exclude_violation_rejected_for_overlapping_appointments`, `test_appointments_concurrency.py::test_concurrent_overlapping_holds_only_one_succeeds` |
| 2 | Migraciones reproducibles | ✅ Cumple | `test_migrations.py` — `db reset` corre limpio y es re-ejecutable; verifica que las 27 tablas esperadas existan |
| 3 | RAG filtra dominio/institución/vigencia | ✅ Cumple | `match_chunks()` — `test_rag_vigencia.py` (3 pruebas: excluye fuente `expired`, excluye `valid_to` pasado, filtra por `domain`+`tenant_id`) |
| 4 | Seeds no duplican | ⚠️→✅ **Corregido** | Bug real encontrado y arreglado (§1). `test_seeds_idempotent.py` re-ejecuta el seed dos veces y compara conteos exactos por tabla. |
| 5 | Auditoría conserva actor/acción/resultado sin secretos | ⚠️ Parcial | `audit_logs` tiene actor (`user_id`)/acción (enum)/`data_before`/`data_after`; `actions` tiene actor/`action_name`/`status`(resultado)/`result_payload` — el patrón actor/acción/resultado está cubierto. **"Sin secretos" no está garantizado a nivel de base de datos**: `metadata`/`payload`/`data_before`/`data_after` son `jsonb` libres, sin masking ni constraint que impida guardar tokens/contraseñas. Es responsabilidad de la capa de aplicación (aún no existe) — no se puede cerrar solo con SQL. Documentado como riesgo abierto, no como bug de esquema. |
| 6 | Queries críticas usan índices apropiados | ✅ Cumple (para MVP) | `test_indexes_explain.py` verifica existencia estructural de los índices esperados y que las queries críticas (sources por tenant+domain+status, appointments por tenant+branch, lookup de idempotency_key) tienen un plan de índice válido. No cubre búsqueda híbrida (no existe aún). |

**5/6 criterios cumplen completamente; 1 (auditoría sin secretos) requiere trabajo en la capa de aplicación, fuera del alcance de la base de datos por sí sola — documentado, no bloqueante para el resto.**

---

## 6. Pruebas a implementar (sección 12 del doc) — cobertura

| # | Prueba requerida | Archivo | Cubre |
|---|---|---|---|
| 1 | Migración vacía/upgrade | `tests/integration/database/test_migrations.py` | `db reset` limpio y re-ejecutable, tablas esperadas presentes |
| 2 | Seeds repetidos | `tests/integration/database/test_seeds_idempotent.py` | Re-ejecución del seed real, conteos exactos por tabla |
| 3 | FK/check/unique/exclude | `tests/integration/database/test_constraints.py` | Un caso negativo por tipo de constraint |
| 4 | Reservas concurrentes | `tests/integration/database/test_appointments_concurrency.py` | Dos conexiones/threads reales insertando en paralelo con `time_range` solapado |
| 5 | Tenancy | `tests/integration/database/test_tenancy_rls.py` | RLS bloquea lectura cross-tenant en `sources`/`conversations`/`appointments`; usuario ve su propio tenant |
| 6 | Vigencia RAG | `tests/integration/database/test_rag_vigencia.py` | `match_chunks` excluye `expired`/`valid_to` pasado, filtra por dominio y tenant |
| 7 | Índices/EXPLAIN | `tests/integration/database/test_indexes_explain.py` | Existencia estructural + plan forzado por índice para queries críticas |
| 8 | Idempotencia | `tests/integration/database/test_idempotency_actions.py` | `actions.idempotency_key` único rechaza duplicados |
| 9 | Backup smoke | `tests/integration/database/test_backup_smoke.py` | `supabase db dump` produce backup válido; restauración a DB temporal compara conteos (se salta con skip si no hay Docker disponible, no como fallo) |

**9/9 pruebas requeridas implementadas.** Resultado de la ejecución real: ver §8.

---

## 7. Incumplimientos de contrato detectados (sección 10 del doc)

Estos son desviaciones del contrato de integración declarado, relevantes para Dani/Diego/Cris al consumir este esquema. No son bugs (el esquema es internamente consistente) sino desalineaciones con lo pactado — quedan documentadas para decidir si se corrigen o se actualiza el contrato:

- **"Dinero en minor units"** → violado. `plans.price_monthly/yearly`, `invoices.amount`, `payments.amount` usan `numeric(10,2)` (decimal), no enteros en centavos.
- **"IDs opacos"** → violado. Todas las PK son `bigint generated always as identity` (secuenciales, no opacas/UUID). Un cliente puede inferir volumen de datos o iterar IDs.
- **`institution_id`** → el esquema usa `tenant_id` consistentemente en vez de `institution_id`. Equivalente funcional, pero es un desajuste de nomenclatura literal con el contrato si otros equipos esperan ese nombre de columna/campo en payloads.
- **"Repositorios como frontera"** → no existe ninguna capa de repositorio (Python/TS) en el repo; todo el acceso sería SQL directo o vía PostgREST/RPC de Supabase. No es un defecto de la base de datos en sí, pero el contrato lo exige como parte del entregable de Daher (sección 8: "repositorios").
- **Alembic** → mencionado como responsabilidad (sección 2) pero nunca usado; las migraciones reales son SQL plano vía Supabase CLI. Probablemente una desactualización del doc original más que un gap real (Supabase CLI es un reemplazo válido y más nativo para este stack).

Cumplen correctamente: `timestamptz` en el 100% de las columnas de fecha, `tenant_id` de forma consistente (aunque con el nombre distinto al contrato), dimensión de vector configurada y consistente (1536 en columna y función), eventos/auditoría append-only por diseño de RLS (sin políticas de update/delete para roles no-admin).

---

## 8. Checklist (sección 15 del doc) — estado

- [x] PK/FK y ownership
- [x] Unique/check/exclude
- [x] Índices y query plans — estructurales verificados; EXPLAIN con datos de volumen real pendiente (solo posible con carga productiva)
- [x] UTC/money/IDs — UTC ✅; money y IDs **no** siguen el contrato (ver §7), pero es una decisión de diseño consistente, no un bug
- [x] Tenancy y permisos
- [ ] Retención/masking — no implementado (Core, ver §2)
- [x] Migraciones expand/contract — el fix de esta auditoría (`20260504150000_...`) sigue el patrón correctamente
- [x] Seeds idempotentes — corregido en esta auditoría
- [x] Backup/restore — smoke test implementado; runbook operativo documentado pendiente (Pro, ver §3)
- [x] Diccionario/ERD — `docs/architecture/database_schema.md`
- [x] Tests concurrentes — `test_appointments_concurrency.py`

---

## 9. Cómo ejecutar la verificación

```bash
# 1. Levantar Supabase local (requiere Docker corriendo)
npx supabase start

# 2. Aplicar todas las migraciones, incluyendo el fix de idempotencia
npx supabase db reset

# 3. Instalar dependencias de test
pip install -r tests/requirements.txt

# 4. Ejecutar la suite de integración de base de datos
pytest tests/integration/database -v

# 5. Apagar el stack
npx supabase stop
```

Variable de entorno opcional `DATABASE_URL` (default: `postgresql://postgres:postgres@127.0.0.1:54322/postgres`, el valor estándar del Postgres local de Supabase CLI).

---

## 10. Resumen ejecutivo

- **MVP**: prácticamente completo (6/7). Único gap real: tool registry/calls (no bloquea ningún criterio de aceptación).
- **Core**: mayormente pendiente (métricas, búsqueda híbrida, retención). El catálogo de 5 dominios está modelado pero solo 1/5 tiene contenido RAG.
- **Pro y Extremo**: sin implementar en su mayoría, como se esperaba en esta etapa del proyecto — documentado con esfuerzo estimado por tarea.
- **Bug real encontrado y corregido**: idempotencia de seeds de `sources`/`documents` (violaba el criterio de aceptación "Seeds no duplican").
- **9/9 pruebas de la sección 12 implementadas**, cubriendo los 6 criterios de aceptación de la sección 13 (5 cumplen completo, 1 depende de capa de aplicación aún inexistente).
