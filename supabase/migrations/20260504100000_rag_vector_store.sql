-- =============================================================================
-- SaaS v1.3.0 — Módulo RAG & Vector Store (pgvector)
-- Fuentes institucionales, documentos, chunks y embeddings vector(1536)
-- =============================================================================

create extension if not exists vector;

-- Fuentes institucionales documentales
create table if not exists public.sources (
  id            bigint primary key generated always as identity,
  tenant_id     bigint      not null references public.tenants (id) on delete cascade,
  domain        text        not null check (domain in ('vehiculos', 'ayuntamiento_empresas', 'registro_civil', 'salud', 'ganaderia', 'general')),
  name          text        not null,
  publisher     text,
  source_url    text,
  version       text        not null default 'v1.0',
  status        text        not null default 'active' check (status in ('active', 'expired', 'deprecated', 'draft')),
  valid_from    timestamptz not null default now(),
  valid_to      timestamptz,
  checksum      text        not null,
  metadata      jsonb       not null default '{}',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- Documentos institucionales dentro de una fuente
create table if not exists public.documents (
  id            bigint primary key generated always as identity,
  tenant_id     bigint      not null references public.tenants (id) on delete cascade,
  source_id     bigint      not null references public.sources (id) on delete cascade,
  title         text        not null,
  content_raw   text,
  file_id       bigint      references public.files (id) on delete set null,
  metadata      jsonb       not null default '{}',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- Chunks vectorizados con embeddings vector(1536)
create table if not exists public.chunks (
  id            bigint primary key generated always as identity,
  tenant_id     bigint      not null references public.tenants (id) on delete cascade,
  document_id   bigint      not null references public.documents (id) on delete cascade,
  domain        text        not null,
  chunk_index   int         not null default 0,
  content       text        not null,
  embedding     vector(1536),
  checksum      text,
  metadata      jsonb       not null default '{}',
  created_at    timestamptz not null default now()
);

-- Índices HNSW para búsqueda vectorial rápida por distancia coseno
create index if not exists idx_chunks_embedding_hnsw 
  on public.chunks 
  using hnsw (embedding vector_cosine_ops);

create index if not exists idx_sources_tenant_domain on public.sources (tenant_id, domain, status);
create index if not exists idx_documents_source      on public.documents (source_id);
create index if not exists idx_chunks_document        on public.chunks (document_id);
create index if not exists idx_chunks_tenant_domain   on public.chunks (tenant_id, domain);

-- Trigger updated_at
drop trigger if exists set_updated_at on public.sources;
create trigger set_updated_at before update on public.sources for each row execute procedure public.set_updated_at();

drop trigger if exists set_updated_at on public.documents;
create trigger set_updated_at before update on public.documents for each row execute procedure public.set_updated_at();

-- Función RPC para búsqueda vectorial por similitud de coseno en RAG
create or replace function public.match_chunks(
  query_embedding vector(1536),
  match_threshold float default 0.6,
  match_count int default 5,
  filter_domain text default null,
  filter_tenant_id bigint default null
)
returns table (
  id bigint,
  document_id bigint,
  domain text,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable security definer
set search_path = public
as $$
  select
    c.id,
    c.document_id,
    c.domain,
    c.content,
    c.metadata,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.chunks c
  join public.documents d on d.id = c.document_id
  join public.sources s on s.id = d.source_id
  where (filter_tenant_id is null or c.tenant_id = filter_tenant_id)
    and (filter_domain is null or c.domain = filter_domain)
    and s.status = 'active'
    and (s.valid_to is null or s.valid_to > now())
    and (1 - (c.embedding <=> query_embedding)) >= match_threshold
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

-- RLS
alter table public.sources   enable row level security;
alter table public.documents enable row level security;
alter table public.chunks    enable row level security;

drop policy if exists "sources: select own" on public.sources;
create policy "sources: select own" on public.sources for select to authenticated using (tenant_id = (select public.current_tenant_id()));

drop policy if exists "documents: select own" on public.documents;
create policy "documents: select own" on public.documents for select to authenticated using (tenant_id = (select public.current_tenant_id()));

drop policy if exists "chunks: select own" on public.chunks;
create policy "chunks: select own" on public.chunks for select to authenticated using (tenant_id = (select public.current_tenant_id()));
