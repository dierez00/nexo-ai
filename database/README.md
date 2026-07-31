# Base de datos

## Objetivo

Definir persistencia relacional/vectorial, migraciones Supabase, seeds y garantías de integridad multi-tenant RLS.

## Documentación Completa del Esquema

La especificación técnica detallada, diccionario de datos, funciones RPC, índices y políticas RLS se encuentran en:
- [docs/architecture/database_schema.md](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/docs/architecture/database_schema.md)

## Migraciones Supabase (`supabase/migrations`)

1. [`20260504094442_initial_schema.sql`](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/supabase/migrations/20260504094442_initial_schema.sql): Multi-tenant, Subscripciones, Roles/Permisos RBAC, Usuarios, Sucursales, Auditoría y Facturación.
2. [`20260504100000_rag_vector_store.sql`](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/supabase/migrations/20260504100000_rag_vector_store.sql): Módulo RAG & Vector Store (`pgvector` 1536d, índice HNSW, `match_chunks`).
3. [`20260504110000_appointments_gist.sql`](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/supabase/migrations/20260504110000_appointments_gist.sql): Citas y Holds con constraint de exclusión GiST (`btree_gist`).
4. [`20260504120000_conversations_runs_events.sql`](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/supabase/migrations/20260504120000_conversations_runs_events.sql): Conversaciones, Mensajes (A2UI), Trazabilidad de Runs/Eventos, Acciones idempotentes y LangGraph checkpoints.
5. [`20260504130000_evaluations_judge.sql`](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/supabase/migrations/20260504130000_evaluations_judge.sql): Evaluaciones LLM-as-Judge.
6. [`20260504140000_seeds_demo.sql`](file:///c:/Users/di3go/Downloads/metaphorce-retos/nexo-ai/supabase/migrations/20260504140000_seeds_demo.sql): Seeds de demostración (Vehículos y Apertura de Empresas).

## Convenciones

`snake_case`, IDs opacos, `timestamptz`, dinero en minor units, `tenant_id`, RLS dinámico por tenant, migraciones expand/contract y seeds idempotentes.

## Dependencias y responsable

PostgreSQL/pgvector/Supabase Auth y contratos de persistencia. Responsable: Daher.

## Terminado

Migrar desde cero y actualizar funciona (`npx supabase db reset`); dos reservas concurrentes no se solapan (`btree_gist`); seeds no duplican y RLS aisla tenants estrictamente.

