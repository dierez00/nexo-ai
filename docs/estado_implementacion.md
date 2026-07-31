# Estado de implementación — nexo-ai

> **Propósito.** Documento único de consulta que cruza la **documentación** del repo
> contra el **código real** y marca qué apartados están completados. Sirve como
> fuente de verdad rápida para saber, sin abrir 100 archivos, qué está hecho, qué es
> mock y qué falta.
>
> **Snapshot:** 2026-07-31 · **Responsable de mantenerlo:** Dani (coordina docs). ·
> **Ámbito:** todo el repo (Cris, Dani, Daher, Diego) y las fases MVP → Extremo.
>
> Este es un *snapshot*: al cambiar el código hay que revalidar las filas afectadas.
> No sustituye a los planes de `docs/team/`; los resume y los ancla al código.

## Leyenda de estados

| Símbolo | Significado |
|---|---|
| ✅ **Implementado** | Código real en el repo, trazable a archivo y (salvo nota) cubierto por pruebas. |
| ⚠️ **Mock** | Funciona de extremo a extremo pero con dobles deterministas: no hay llamada externa real. |
| ⏳ **Pendiente** | Planeado en la documentación, aún sin implementar. |

---

## 1. Resumen ejecutivo por fase

Fases según `Nexo_IA_Arquitectura_y_Plan.md §10` y los planes de equipo.

| Fase | Estado | Notas |
|---|---|---|
| **Fase 0 — preparación** | ✅ Implementado | Contratos tipados, puertos, dobles de prueba, grafo mínimo verificable offline. |
| **Fase 1 — MVP** | ✅ Implementado (con deuda) | Recorridos `CAP-VEH-01` y `CAP-EMP-01` E2E sin credenciales. Deuda: cola durable y adapters institucionales reales. |
| **Fase 2 — Core** | ⏳ Parcial | Base presente (dominios, workflow, dashboards admin); faltan los 5 dominios completos y filtros/estados avanzados. |
| **Fase 3 — Pro** | ⏳ Parcial | Endpoint de voz y A2UI existen; MCP Mapper, model router con backends reales y formularios A2UI dinámicos pendientes. |
| **Fase 4 — Extremo** | ⏳ Pendiente | Paralelismo de nodos, mini-RAGs, LLM-as-judge, personalización avanzada, builder visual. |

**Titular:** el repo es un **MVP funcional**, no un scaffold. El flujo núcleo
(ciudadano → chat → clasificación → confirmación idempotente → ejecución) está
implementado y probado de extremo a extremo con dobles.

---

## 2. Estado por módulo / área

### 2.1 Backend API — FastAPI (Dani)

Rutas base: `backend/src/nexo_api/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Router auth (login, refresh, crear usuario, `users/me`) | ✅ | `api/v1/auth.py` |
| Router conversations (crear, listar, postear mensaje → 202) | ✅ | `api/v1/conversations.py` |
| Router runs (listar, snapshot, timeline, **SSE** con `Last-Event-ID`) | ✅ | `api/v1/runs.py` |
| Router actions (confirmación idempotente + conflicto de versión) | ✅ | `api/v1/actions.py` |
| Router appointments (disponibilidad + holds con conflicto) | ✅ | `api/v1/appointments.py` |
| Router voice (turno síncrono, server-tool ElevenLabs) | ✅ | `api/v1/voice.py` |
| Router admin (métricas, catálogo, config, tenant-scoped) | ✅ | `api/v1/admin.py` |
| Health (`/health/live`, `/health/ready` con chequeo de DB) | ✅ | `api/health.py` |
| Webhooks Twilio (inbound WhatsApp + status, validación de firma) | ✅ | `api/webhooks.py` |
| Idempotencia (replay por `Idempotency-Key`) | ✅ | `services/idempotency.py`, `repositories/idempotency.py` |
| Rate limiting (token bucket por usuario/IP) | ✅ | `core/rate_limit.py` |
| Problem Details (RFC 7807) + middleware trace-id/CORS | ✅ | `core/errors.py`, `core/middleware.py` |
| Persistencia async SQLAlchemy (repos de todas las tablas núcleo) | ✅ | `repositories/*.py`, `core/db.py` |
| Seguridad JWT por JWKS (Supabase, ES256/RS256) | ✅ | `core/security.py`, `api/deps.py` |

### 2.2 Frontend web — Next.js (Cris)

Rutas base: `apps/web/src/`. Stack: Next 16, React 19, TS 5, Tailwind 4.

| Apartado | Estado | Evidencia |
|---|---|---|
| Rutas públicas/portal (login, portal, chat, citas, seguimiento, trámite) | ✅ | `app/login/`, `app/portal/*/page.tsx` |
| Rutas admin (panel, catálogo, runs, workflow, a2ui-lab, integraciones) | ✅ | `app/admin/*/page.tsx` |
| Agente de voz | ✅ | `app/agente-voz/page.tsx` |
| Chat con SSE reanudable + tarjetas de acción pendiente | ✅ | `app/portal/chat/`, `features/chat/*` |
| Render de superficie A2UI (formularios dinámicos desde run) | ✅ | `features/a2ui/SurfaceFromRun.tsx` |
| Cliente de contratos (fetch auth, idempotency-key, SSE) | ✅ | `lib/api/client.ts` |
| Shells, dark mode, status badges | ✅ | `components/nexo/*` |
| **Base de pruebas frontend + CI de frontend** | ⏳ | Gate F0 **no cumplido** — deuda más urgente según `docs/team/cris_plan_implementacion_hasta_extremo.md §7.7`. |

### 2.3 Orquestación y agentes (Diego)

Rutas base: `orchestration/src/nexo_orchestration/`, `agents/src/nexo_agents/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Grafo mínimo Fase 0 (classify → finalize) | ✅ | `graph/minimal.py` |
| Grafo MVP 12 nodos (normalize…finalize) con checkpoints | ✅ | `graph/mvp.py` |
| Reanudación por `completed_nodes` + interrupción → `waiting_confirmation` | ✅ | `graph/mvp.py` |
| Emisión de `RunEvent` con redacción `public_data` para SSE | ✅ | `graph/mvp.py` |
| Agentes: classifier, navigator, verifier, writer, estimator, transactional | ✅ | `agents/src/nexo_agents/{classifier,navigator,verifier,writer,estimator,transactional}.py` |
| Catálogo central (dominios/tools/prompts versionados), skills, safety | ✅ | `agents/src/nexo_agents/{catalog,skills,health_safety,prompts}.py` |
| **Paralelismo de nodos** (verificador/estimador en paralelo) | ⏳ | MVP es secuencial (Fase 4). |
| **Model router con backends reales** | ⏳ | Gateway existe; llamadas reales de modelo pendientes (Pro). |

### 2.4 RAG (Diego)

Rutas base: `rag/src/nexo_rag/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Ingesta y chunking de corpus | ✅ | `corpus/ingestion.py`, `corpus/chunking.py` |
| Embeddings | ✅ | `embeddings.py` |
| Retrieval híbrido (semántico + léxico) | ✅ | `retrieval/hybrid.py`, `retrieval/lexical.py` |
| Suficiencia y safety | ✅ | `retrieval/sufficiency.py`, `safety.py` |
| Evaluación / baseline | ✅ | `evaluation.py`, `baseline.py` |
| **Mini-RAGs por dominio** | ⏳ | Fase 4 (Extremo). |

### 2.5 MCP (Diego)

Rutas base: `mcp/src/nexo_mcp/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Catálogo de tools, ejecución, autorización, server, definiciones | ✅ | `catalog.py`, `execution.py`, `authorization.py`, `server.py`, `tools/definitions.py` |
| **MCP Mapper** (mapeo dinámico de capacidades) | ⏳ | Fase 3 (Pro). |

### 2.6 A2UI (Diego / Cris)

Rutas base: `a2ui/src/nexo_a2ui/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Builder de superficie ciudadana | ✅ | `builder.py` |
| Validador de superficie | ✅ | `validator.py` |
| Catálogo `citizen:v1` (congelado) + fallback | ✅ | `catalog.py`, `fallback.py`, `a2ui/catalogs/citizen/v1/catalog.json` |
| **Formularios A2UI dinámicos** + superficies admin generadas | ⏳ | Fase 3 (Pro). |

### 2.7 Contratos

Rutas base: `contracts/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Modelos Pydantic tipados (RunRequest/Result/Event, ActionRequest, …) | ✅ | `contracts/` |
| Export a JSON Schema + eventos v1 | ✅ | `contracts/jsonschema/`, `contracts/events/` |
| OpenAPI sin drift (verificado por prueba) | ✅ | `contracts/openapi/v1.yaml`, `backend/tests/test_openapi_no_drift.py` |
| Reglas de compatibilidad y changelog | ✅ | `contracts/CHANGELOG.md`, `docs/architecture/conventions.md` |

### 2.8 Base de datos (Daher)

Rutas base: `database/`, `supabase/migrations/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Esquema inicial SaaS v1.3.0 (21 tablas multi-tenant + RLS) | ✅ | `database/20260504094442_initial_schema.sql` |
| Migraciones incrementales (RAG vector store, appointments GiST, eventos, ledger) | ✅ | `supabase/migrations/*.sql` (17 migraciones) |
| Seeds demo idempotentes | ✅ | `database/seeds/seed_demo.sql`, `scripts/seed_demo.py` |
| Auditoría de esquema/integridad | ✅ Documentada | `docs/team/daher_auditoria_base_datos.md` |

### 2.9 Integraciones

Rutas base: `integrations/src/nexo_integrations/`.

| Apartado | Estado | Evidencia |
|---|---|---|
| Twilio WhatsApp (firma `X-Twilio-Signature` + dedup por `provider_message_id`) | ✅ | `twilio/webhook.py` |
| Supabase Auth (cliente, sesión, JWKS) | ✅ | `supabase/client.py` |
| **Adapters institucionales** (vehículos, apertura de empresas, …) | ⚠️ Mock | `institutional/__init__.py` (placeholder; respuestas deterministas) |
| Adapters de modelos / storage | ⏳ | `models/__init__.py`, `storage/__init__.py` (placeholders) |

### 2.10 Observabilidad, infra, pruebas y scripts

| Apartado | Estado | Evidencia |
|---|---|---|
| Logging JSONL + convenciones de eventos | ✅ | `observability/README.md` |
| Docker / Compose (`api`, perfil `local-db` pgvector) | ✅ | `infrastructure/docker/Dockerfile`, `docker-compose.yml` |
| Despliegue Railway + runbook de arranque/rollback | ✅ | `docs/runbooks/arranque.md` |
| Suites de pruebas backend (health, auth, conv, actions, appts, SSE, voice, webhooks, rate-limit, e2e orquestador) | ✅ | `backend/tests/test_*.py` |
| Scripts de seed / calidad (`lint`, `test`) | ✅ | `scripts/seed_demo.py`, `scripts/{lint,test}.{sh,ps1}` |
| `run.sh` (arranque unificado) | ⏳ | Declarado pendiente en `README.md` §"Dependencias, ejemplos y tareas". |

---

## 3. Deuda técnica y pendientes prioritarios

Extraídos de declaraciones explícitas en la propia documentación:

1. **Worker / cola durable.** El streaming SSE del MVP corre **en proceso**; un
   reinicio de la API cancela runs activos. No hay cola durable.
   *(`README.md` §Estado de ejecución; `docs/runbooks/arranque.md` §6.)*
2. **Adapters institucionales reales.** Hoy son mock deterministas; falta integración
   real. *(`README.md`; `integrations/.../institutional/`.)*
3. **Base de pruebas + CI de frontend.** Gate F0 de Cris no cumplido; es la deuda
   más urgente de su plan. *(`docs/team/cris_plan_implementacion_hasta_extremo.md §7.7`.)*
4. **Model router con backends reales** y **paralelismo de nodos** (MVP secuencial).

---

## 4. Índice de fuentes

Dónde ampliar cada apartado de este resumen.

| Tema | Documento fuente |
|---|---|
| Arquitectura, contratos, fases, checklist general | `Nexo_IA_Arquitectura_y_Plan.md` (§10 fases, §14 checklist) |
| Propuesta, alcance y rúbrica | `Nexo_IA_Propuesta_Completa.md` |
| Convenciones transversales (IDs, wire, errores, PII) | `docs/architecture/conventions.md` |
| Esquema de base de datos | `docs/architecture/database_schema.md` |
| Decisiones (LangGraph, model gateway, RAG, MCP, A2UI, idempotencia) | `docs/adr/000{2..7}-*.md` |
| Planes por persona | `docs/team/{cris,dani,daher,diego}_*.md` |
| Hallazgos por fase | `docs/team/fase{0,1,2}_hallazgos.md` |
| Arranque, despliegue, rollback | `docs/runbooks/arranque.md` |
| WhatsApp Twilio Sandbox | `docs/runbooks/twilio_whatsapp.md` |
| Agente de voz | `docs/elevenlabs_voice_agent.md` |
| READMEs por módulo | `<módulo>/README.md` (backend, agents, rag, mcp, a2ui, contracts, …) |
