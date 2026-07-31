-- =============================================================================
-- SaaS v1.3.0 — Módulo Conversaciones, Trazo de Ejecución (Runs), Eventos & Idempotencia
-- Soporte multicanal (web, whatsapp, voice), checkpoints de LangGraph y acciones transaccionales
-- =============================================================================

-- Tabla de conversaciones
create table if not exists public.conversations (
  id          bigint primary key generated always as identity,
  tenant_id   bigint      not null references public.tenants (id) on delete cascade,
  user_id     bigint      references public.users (id) on delete set null,
  channel     text        not null default 'web' check (channel in ('web', 'whatsapp', 'voice', 'admin')),
  title       text,
  status      text        not null default 'active' check (status in ('active', 'archived', 'closed')),
  metadata    jsonb       not null default '{}',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Mensajes intercambiados por cualquier canal
create table if not exists public.messages (
  id              bigint primary key generated always as identity,
  conversation_id bigint      not null references public.conversations (id) on delete cascade,
  sender_type     text        not null check (sender_type in ('user', 'assistant', 'system')),
  content         text        not null,
  a2ui_payload    jsonb,      -- JSON de la superficie A2UI si aplica
  metadata        jsonb       not null default '{}',
  created_at      timestamptz not null default now()
);

-- Ejecución de un Run del Supervisor Multiagente (Trazabilidad)
create table if not exists public.runs (
  id              bigint primary key generated always as identity,
  trace_id        text        not null unique,
  tenant_id       bigint      not null references public.tenants (id) on delete cascade,
  conversation_id bigint      references public.conversations (id) on delete set null,
  domain          text,
  intents         jsonb       not null default '[]',
  plan            jsonb       not null default '[]',
  status          text        not null default 'running' check (status in ('running', 'completed', 'failed', 'requires_action')),
  model_selected  text,
  latency_ms      int,
  total_cost_usd  numeric(10,6) default 0,
  metadata        jsonb       not null default '{}',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- Eventos de ejecución granular por cada nodo del grafo
create table if not exists public.run_events (
  id          bigint primary key generated always as identity,
  run_id      bigint      not null references public.runs (id) on delete cascade,
  trace_id    text        not null,
  event_type  text        not null, -- p.ej. 'node_start', 'node_end', 'mcp_call', 'rag_retrieval', 'error'
  node_name   text        not null,
  payload     jsonb       not null default '{}',
  created_at  timestamptz not null default now()
);

-- Registro de Acciones Transaccionales e Idempotencia
create table if not exists public.actions (
  id              bigint primary key generated always as identity,
  tenant_id       bigint      not null references public.tenants (id) on delete cascade,
  user_id         bigint      references public.users (id) on delete set null,
  idempotency_key text        not null unique,
  action_name     text        not null, -- p.ej. 'vehiculos.reservar_cita', 'ayuntamiento.crear_solicitud'
  payload         jsonb       not null default '{}',
  status          text        not null default 'pending' check (status in ('pending', 'completed', 'failed')),
  result_folio    text,
  result_payload  jsonb,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- Checkpoints de LangGraph para reanudación de estados
create table if not exists public.langgraph_checkpoints (
  thread_id     text        primary key,
  checkpoint_id text        not null,
  parent_id     text,
  checkpoint    jsonb       not null,
  metadata      jsonb       not null default '{}',
  created_at    timestamptz not null default now()
);

-- Índices de performance
create index if not exists idx_conversations_tenant_user on public.conversations (tenant_id, user_id);
create index if not exists idx_messages_conversation      on public.messages (conversation_id, created_at);
create index if not exists idx_runs_tenant_trace         on public.runs (tenant_id, trace_id);
create index if not exists idx_run_events_run             on public.run_events (run_id, created_at);
create index if not exists idx_actions_idempotency        on public.actions (idempotency_key);

-- Triggers updated_at
drop trigger if exists set_updated_at on public.conversations;
create trigger set_updated_at before update on public.conversations for each row execute procedure public.set_updated_at();

drop trigger if exists set_updated_at on public.runs;
create trigger set_updated_at before update on public.runs for each row execute procedure public.set_updated_at();

drop trigger if exists set_updated_at on public.actions;
create trigger set_updated_at before update on public.actions for each row execute procedure public.set_updated_at();

-- RLS Policies
alter table public.conversations          enable row level security;
alter table public.messages               enable row level security;
alter table public.runs                   enable row level security;
alter table public.run_events             enable row level security;
alter table public.actions                enable row level security;
alter table public.langgraph_checkpoints  enable row level security;

drop policy if exists "conversations: select own" on public.conversations;
create policy "conversations: select own" on public.conversations for select to authenticated using (tenant_id = (select public.current_tenant_id()));

drop policy if exists "messages: select own" on public.messages;
create policy "messages: select own" on public.messages for select to authenticated using (exists (select 1 from public.conversations c where c.id = conversation_id and c.tenant_id = (select public.current_tenant_id())));

drop policy if exists "runs: select own" on public.runs;
create policy "runs: select own" on public.runs for select to authenticated using (tenant_id = (select public.current_tenant_id()));

drop policy if exists "run_events: select own" on public.run_events;
create policy "run_events: select own" on public.run_events for select to authenticated using (exists (select 1 from public.runs r where r.id = run_id and r.tenant_id = (select public.current_tenant_id())));

drop policy if exists "actions: select own" on public.actions;
create policy "actions: select own" on public.actions for select to authenticated using (tenant_id = (select public.current_tenant_id()));
