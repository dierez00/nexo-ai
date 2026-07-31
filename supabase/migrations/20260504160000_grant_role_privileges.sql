-- =============================================================================
-- SaaS v1.3.0 — Fix: privilegios de rol faltantes (GRANT) para anon/
-- authenticated/service_role
-- =============================================================================
-- Ninguna migración anterior otorgó GRANT de SELECT/INSERT/UPDATE/DELETE a
-- `authenticated` ni a `service_role` sobre ninguna tabla de `public`
-- (verificado: information_schema.role_table_grants solo listaba
-- TRIGGER/TRUNCATE/REFERENCES, heredados por defecto). En Postgres el GRANT
-- a nivel de tabla se evalúa ANTES que las políticas RLS: sin él, la
-- consulta falla con "permission denied" sin importar cuán permisiva sea la
-- política. Esto dejaba las políticas RLS de todas las migraciones
-- anteriores completamente inertes — incluyendo para `service_role`, que
-- tiene `rolbypassrls = true` pero igual necesita el GRANT para tocar la
-- tabla. En la práctica, ni el backend (`service_role`) ni ningún usuario
-- autenticado podían leer o escribir una sola fila.
-- =============================================================================

grant usage on schema public to anon, authenticated, service_role;

-- service_role: acceso total. Bypassa RLS (rolbypassrls) por diseño de
-- Supabase, pero requiere el GRANT de todas formas para poder operar como
-- backend de confianza sobre cualquier tabla, incluidas las que no tienen
-- ninguna política para `authenticated` (p.ej. `langgraph_checkpoints`).
grant all privileges on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to service_role;
alter default privileges in schema public grant all privileges on tables to service_role;
alter default privileges in schema public grant usage, select on sequences to service_role;

-- authenticated: privilegios exactos que reflejan las políticas RLS ya
-- declaradas (least privilege — ver "create policy" en las migraciones
-- anteriores). No se otorga nada sobre `langgraph_checkpoints` porque esa
-- tabla no tiene ninguna política para `authenticated` (bloqueo intencional).
grant select on
  public.tenants,
  public.tenant_domains,
  public.plans,
  public.modules,
  public.plan_modules,
  public.subscriptions,
  public.tenant_modules,
  public.roles,
  public.permissions,
  public.role_permissions,
  public.branches,
  public.invoices,
  public.payments,
  public.invites,
  public.sources,
  public.documents,
  public.chunks,
  public.conversations,
  public.messages,
  public.runs,
  public.run_events,
  public.actions,
  public.judge_results
to authenticated;

grant select, update on public.users to authenticated;
grant select, insert on public.audit_logs to authenticated;
grant select, insert on public.files to authenticated;
grant select, insert, update on public.appointments to authenticated;
