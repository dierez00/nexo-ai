-- =============================================================================
-- SaaS v1.3.0 — Seeds de Demostración (Vehículos y Apertura de Empresas)
-- Datos iniciales idempotentes para pruebas E2E en Supabase
-- =============================================================================

-- 1. Tenant Demo
insert into public.tenants (name, slug, status)
values ('Gobierno del Estado (Demo)', 'gobierno-demo', 'active')
on conflict (slug) do update set name = excluded.name;

-- 2. Planes
insert into public.plans (code, name, description, max_users, max_modules, is_default)
values ('enterprise', 'Plan Institucional Enterprise', 'Acceso a los 5 dominios y capacidades MCP', null, null, true)
on conflict (code) do update set name = excluded.name;

-- 3. Módulos
insert into public.modules (code, name, description, is_core)
values 
  ('vehiculos', 'Control Vehicular', 'Renovación de licencias, adeudos y citas de trámite', true),
  ('ayuntamiento_empresas', 'Apertura de Empresas', 'Licencias de funcionamiento y permiso de suelo', true),
  ('registro_civil', 'Registro Civil', 'Actas de nacimiento, matrimonio y aclaraciones', false),
  ('salud', 'Servicios de Salud', 'Ubicación de unidades de salud y orientación', false),
  ('ganaderia', 'Gestión Ganadera', 'Movilización y registros sanitarios', false)
on conflict (code) do update set name = excluded.name;

-- 4. Sucursal Demo
insert into public.branches (tenant_id, code, name, address, status)
select t.id, 'MOD-CENTRO', 'Módulo Vehicular y Municipal Centro', 'Av. Principal #100, Col. Centro', 'active'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, code) do update set name = excluded.name;

-- 5. Roles de Sistema
insert into public.roles (tenant_id, code, name, description, is_system)
values 
  (null, 'admin', 'Administrador Global', 'Acceso total al sistema', true),
  (null, 'citizen', 'Ciudadano', 'Usuario final para consulta y trámites', true)
on conflict do nothing;

-- 6. Fuente RAG inicial para Vehículos
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Reglamento de Tránsito y Licencias 2026', 'Secretaría de Finanzas', 'https://finanzas.gob.demo/licencias', 'v2026.1', 'active', 'hash_vehiculos_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict do nothing;

-- 7. Documento inicial RAG
insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos para Renovación de Licencia de Conducir', 'Para renovar la licencia se requiere: 1. Identificación oficial vigente (INE/Pasaporte). 2. Comprobante de domicilio reciente (no mayor a 3 meses). 3. Licencia anterior o reporte de robo. 4. Pago de derechos ($850.00 MXN).'
from public.sources s where s.checksum = 'hash_vehiculos_001'
on conflict do nothing;
