-- =============================================================================
-- SaaS v1.3.0 — Módulo Evaluaciones & LLM-as-Judge
-- Registro de evaluaciones de fidelidad, completitud, claridad y calidad A2UI
-- =============================================================================

create table if not exists public.judge_results (
  id                        bigint primary key generated always as identity,
  run_id                    bigint      not null references public.runs (id) on delete cascade,
  trace_id                  text        not null,
  tenant_id                 bigint      not null references public.tenants (id) on delete cascade,
  judge_model               text        not null,
  domain_correctness_score  numeric(3,2) check (domain_correctness_score >= 0 and domain_correctness_score <= 1),
  fidelity_score            numeric(3,2) check (fidelity_score >= 0 and fidelity_score <= 1),
  completeness_score        numeric(3,2) check (completeness_score >= 0 and completeness_score <= 1),
  clarity_score             numeric(3,2) check (clarity_score >= 0 and clarity_score <= 1),
  a2ui_quality_score        numeric(3,2) check (a2ui_quality_score >= 0 and a2ui_quality_score <= 1),
  hallucinations_detected   boolean     not null default false,
  feedback                  text,
  evaluation_metadata       jsonb       not null default '{}',
  created_at                timestamptz not null default now()
);

create index if not exists idx_judge_results_run    on public.judge_results (run_id);
create index if not exists idx_judge_results_tenant on public.judge_results (tenant_id, created_at desc);

alter table public.judge_results enable row level security;

drop policy if exists "judge_results: select own" on public.judge_results;
create policy "judge_results: select own" on public.judge_results for select to authenticated using (tenant_id = (select public.current_tenant_id()));
