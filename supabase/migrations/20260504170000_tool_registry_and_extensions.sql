-- Migration: 20260504170000_tool_registry_and_extensions.sql
-- Description: Adds Tool Registry (tools, tool_calls) and supporting Core/Pro/Extremo tables
-- (metric_sets, voice_sessions, prompt_versions, corpus_versions, contradictions)

-- 1. Tool Registry: tools & tool_calls
create table if not exists public.tools (
    id bigint generated always as identity primary key,
    tenant_id bigint not null references public.tenants(id) on delete cascade,
    name text not null,
    description text,
    category text default 'general' not null,
    input_schema jsonb default '{}'::jsonb not null,
    output_schema jsonb default '{}'::jsonb not null,
    is_active boolean default true not null,
    created_at timestamptz default clock_timestamp() not null,
    updated_at timestamptz default clock_timestamp() not null,
    constraint tools_tenant_name_key unique (tenant_id, name)
);

create table if not exists public.tool_calls (
    id bigint generated always as identity primary key,
    run_id bigint references public.runs(id) on delete set null,
    tool_id bigint references public.tools(id) on delete set null,
    trace_id text not null,
    input_payload jsonb default '{}'::jsonb not null,
    output_payload jsonb default '{}'::jsonb not null,
    status text not null check (status in ('pending', 'running', 'success', 'error')),
    duration_ms integer,
    error_message text,
    created_at timestamptz default clock_timestamp() not null
);

-- 2. Core Metrics: metric_sets
create table if not exists public.metric_sets (
    id bigint generated always as identity primary key,
    tenant_id bigint not null references public.tenants(id) on delete cascade,
    metric_type text not null,
    domain text default 'general' not null,
    period_start timestamptz not null,
    period_end timestamptz not null,
    metrics_data jsonb default '{}'::jsonb not null,
    created_at timestamptz default clock_timestamp() not null,
    updated_at timestamptz default clock_timestamp() not null
);

-- 3. Pro Voice: voice_sessions
create table if not exists public.voice_sessions (
    id bigint generated always as identity primary key,
    tenant_id bigint not null references public.tenants(id) on delete cascade,
    conversation_id bigint references public.conversations(id) on delete set null,
    provider text not null,
    external_session_id text,
    duration_seconds integer default 0 not null,
    audio_url text,
    transcript text,
    metadata jsonb default '{}'::jsonb not null,
    created_at timestamptz default clock_timestamp() not null,
    updated_at timestamptz default clock_timestamp() not null
);

-- 4. Extremo Prompts: prompt_versions
create table if not exists public.prompt_versions (
    id bigint generated always as identity primary key,
    name text not null,
    version text not null,
    system_prompt text not null,
    model text not null,
    is_active boolean default true not null,
    created_at timestamptz default clock_timestamp() not null,
    updated_at timestamptz default clock_timestamp() not null,
    constraint prompt_versions_name_version_key unique (name, version)
);

-- 5. Extremo RAG Snapshot: corpus_versions
create table if not exists public.corpus_versions (
    id bigint generated always as identity primary key,
    tenant_id bigint not null references public.tenants(id) on delete cascade,
    version text not null,
    description text,
    snapshot_meta jsonb default '{}'::jsonb not null,
    created_at timestamptz default clock_timestamp() not null,
    constraint corpus_versions_tenant_version_key unique (tenant_id, version)
);

-- 6. Extremo Contradictions: contradictions
create table if not exists public.contradictions (
    id bigint generated always as identity primary key,
    tenant_id bigint not null references public.tenants(id) on delete cascade,
    run_id bigint references public.runs(id) on delete set null,
    source_id_a bigint references public.sources(id) on delete cascade,
    source_id_b bigint references public.sources(id) on delete cascade,
    description text not null,
    severity text default 'warning' not null check (severity in ('info', 'warning', 'critical')),
    status text default 'open' not null check (status in ('open', 'resolved', 'ignored')),
    created_at timestamptz default clock_timestamp() not null
);

-- 7. Link judge_results to prompt_versions
alter table public.judge_results
    add column if not exists prompt_version_id bigint references public.prompt_versions(id) on delete set null;

-- Triggers for updated_at
create trigger set_updated_at before update on public.tools for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.metric_sets for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.voice_sessions for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.prompt_versions for each row execute function public.set_updated_at();

-- Indexes for frequent queries
create index if not exists tools_tenant_idx on public.tools(tenant_id);
create index if not exists tool_calls_run_idx on public.tool_calls(run_id);
create index if not exists metric_sets_tenant_domain_idx on public.metric_sets(tenant_id, domain);
create index if not exists voice_sessions_tenant_idx on public.voice_sessions(tenant_id);
create index if not exists corpus_versions_tenant_idx on public.corpus_versions(tenant_id);
create index if not exists contradictions_tenant_idx on public.contradictions(tenant_id);

-- Row Level Security
alter table public.tools enable row level security;
alter table public.tool_calls enable row level security;
alter table public.metric_sets enable row level security;
alter table public.voice_sessions enable row level security;
alter table public.prompt_versions enable row level security;
alter table public.corpus_versions enable row level security;
alter table public.contradictions enable row level security;

-- Policies
create policy "tools: select own" on public.tools for select using (tenant_id = (auth.jwt() ->> 'tenant_id')::bigint or (auth.jwt() ->> 'role') = 'service_role');
create policy "tool_calls: select own" on public.tool_calls for select using ((auth.jwt() ->> 'role') = 'service_role');
create policy "metric_sets: select own" on public.metric_sets for select using (tenant_id = (auth.jwt() ->> 'tenant_id')::bigint or (auth.jwt() ->> 'role') = 'service_role');
create policy "voice_sessions: select own" on public.voice_sessions for select using (tenant_id = (auth.jwt() ->> 'tenant_id')::bigint or (auth.jwt() ->> 'role') = 'service_role');
create policy "prompt_versions: select all" on public.prompt_versions for select using (true);
create policy "corpus_versions: select own" on public.corpus_versions for select using (tenant_id = (auth.jwt() ->> 'tenant_id')::bigint or (auth.jwt() ->> 'role') = 'service_role');
create policy "contradictions: select own" on public.contradictions for select using (tenant_id = (auth.jwt() ->> 'tenant_id')::bigint or (auth.jwt() ->> 'role') = 'service_role');

-- Role Grants
grant select, insert, update, delete on public.tools to authenticated, service_role;
grant select, insert, update, delete on public.tool_calls to authenticated, service_role;
grant select, insert, update, delete on public.metric_sets to authenticated, service_role;
grant select, insert, update, delete on public.voice_sessions to authenticated, service_role;
grant select, insert, update, delete on public.prompt_versions to authenticated, service_role;
grant select, insert, update, delete on public.corpus_versions to authenticated, service_role;
grant select, insert, update, delete on public.contradictions to authenticated, service_role;
