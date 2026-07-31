-- =============================================================================
-- SaaS v1.3.0 — Fix: idempotencia real de seeds RAG (sources/documents)
-- =============================================================================
-- Los INSERT ... ON CONFLICT DO NOTHING de 20260504140000_seeds_demo.sql para
-- `sources` y `documents` no tenían ninguna unique/exclusion constraint que
-- respaldara el conflicto, por lo que ON CONFLICT DO NOTHING no encontraba
-- nada contra qué comparar y cada re-ejecución del seed duplicaba filas.
-- Con estas constraints, el mismo ON CONFLICT DO NOTHING (sin target
-- explícito, que en Postgres aplica a la violación de cualquier constraint
-- única del target table) ya deduplica correctamente.
-- =============================================================================

alter table public.sources
  add constraint sources_tenant_checksum_key unique (tenant_id, checksum);

alter table public.documents
  add constraint documents_source_title_key unique (source_id, title);
