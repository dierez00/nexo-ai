-- =============================================================================
-- SaaS v1.3.0 — Seed RAG BULK: corpus sintético masivo por dominio (5 módulos)
-- =============================================================================
-- GENERADO por scripts/gen_rag_bulk_seed.py (NO editar a mano; regenerar).
--
-- Amplía el corpus del runtime con 40 fuentes por dominio
-- (~200 fuentes / ~400 documentos / ~400 chunks) para los CINCO dominios:
-- vehiculos, ayuntamiento_empresas, registro_civil, salud y ganaderia.
--
-- Contenido 100% SINTÉTICO de demostración (marcado "(demostración)"): sin
-- PII ni credenciales; cifras ilustrativas, no oficiales. Salud se limita a
-- NAVEGACIÓN ADMINISTRATIVA (domains/salud/safety_policy.yaml).
--
-- Namespace de checksum PROPIO `bulk_<dom>_NNNN` para NO colisionar con los
-- hashes reales `hash_*` (20260504190000) ni con `syn_*` (20260731120000).
--
-- Idempotente por las constraints existentes:
--   sources_tenant_checksum_key (tenant_id, checksum)
--   documents_source_title_key  (source_id, title)
--   chunks_document_chunk_index_key (document_id, chunk_index)
-- Cada dominio incluye fuentes vencidas/sustituidas (expired/superseded)
-- para ejercitar el filtro de vigencia de public.match_chunks.
-- =============================================================================
-- =========================================================================
-- VEHICULOS — 40 fuentes (namespace bulk_veh_*)
-- =========================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Requisitos de Renovación de Licencia — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0001', 'v2026.1', 'active', 'bulk_veh_0001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 1 (demo, bulk_veh_0001)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 2 (demo, bulk_veh_0001)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Tarifario de Trámites Vehiculares — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0002', 'v2026.1', 'active', 'bulk_veh_0002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 1 (demo, bulk_veh_0002)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 2 (demo, bulk_veh_0002)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 3 (demo, bulk_veh_0002)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Consulta de Adeudos y Refrendo — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0003', 'v2026.1', 'active', 'bulk_veh_0003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 1 (demo, bulk_veh_0003)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Módulos de Atención Vehicular — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0004', 'v2026.1', 'active', 'bulk_veh_0004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 1 (demo, bulk_veh_0004)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 2 (demo, bulk_veh_0004)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0004'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Cita Previa Vehicular — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0005', 'v2026.1', 'active', 'bulk_veh_0005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 1 (demo, bulk_veh_0005)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 2 (demo, bulk_veh_0005)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 3 (demo, bulk_veh_0005)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0005'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Reposición de Placas y Tarjeta — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0006', 'v2026.1', 'active', 'bulk_veh_0006'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 1 (demo, bulk_veh_0006)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0006'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Verificación Vehicular Ambiental — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0007', 'v2026.1', 'active', 'bulk_veh_0007'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 1 (demo, bulk_veh_0007)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0007'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 2 (demo, bulk_veh_0007)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0007'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Licencias para Motociclista — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0008', 'v2026.1', 'active', 'bulk_veh_0008'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 1 (demo, bulk_veh_0008)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 2 (demo, bulk_veh_0008)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 3 (demo, bulk_veh_0008)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0008'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'vehiculos', 'Descuentos por Pronto Pago — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0009', 'v2026.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_veh_0009'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 1 (demo, bulk_veh_0009)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0009'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Trámite de Baja Vehicular — variante 1 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0010', 'v2026.1', 'active', 'bulk_veh_0010'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 1 (demo, bulk_veh_0010)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0010'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 2 (demo, bulk_veh_0010)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0010'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Requisitos de Renovación de Licencia — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0011', 'v2026.2', 'active', 'bulk_veh_0011'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 1 (demo, bulk_veh_0011)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 2 (demo, bulk_veh_0011)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 3 (demo, bulk_veh_0011)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0011'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Tarifario de Trámites Vehiculares — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0012', 'v2026.2', 'active', 'bulk_veh_0012'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 1 (demo, bulk_veh_0012)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0012'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Consulta de Adeudos y Refrendo — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0013', 'v2026.2', 'active', 'bulk_veh_0013'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 1 (demo, bulk_veh_0013)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0013'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 2 (demo, bulk_veh_0013)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0013'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Módulos de Atención Vehicular — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0014', 'v2026.2', 'active', 'bulk_veh_0014'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 1 (demo, bulk_veh_0014)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 2 (demo, bulk_veh_0014)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 3 (demo, bulk_veh_0014)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0014'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Cita Previa Vehicular — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0015', 'v2026.2', 'active', 'bulk_veh_0015'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 1 (demo, bulk_veh_0015)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0015'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Reposición de Placas y Tarjeta — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0016', 'v2026.2', 'active', 'bulk_veh_0016'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 1 (demo, bulk_veh_0016)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0016'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 2 (demo, bulk_veh_0016)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0016'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'vehiculos', 'Verificación Vehicular Ambiental — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0017', 'v2026.2', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_veh_0017'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 1 (demo, bulk_veh_0017)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 2 (demo, bulk_veh_0017)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 3 (demo, bulk_veh_0017)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0017'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Licencias para Motociclista — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0018', 'v2026.2', 'active', 'bulk_veh_0018'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 1 (demo, bulk_veh_0018)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0018'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Descuentos por Pronto Pago — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0019', 'v2026.2', 'active', 'bulk_veh_0019'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 1 (demo, bulk_veh_0019)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0019'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 2 (demo, bulk_veh_0019)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0019'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Trámite de Baja Vehicular — variante 2 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0020', 'v2026.2', 'active', 'bulk_veh_0020'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 1 (demo, bulk_veh_0020)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 2 (demo, bulk_veh_0020)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 3 (demo, bulk_veh_0020)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0020'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Requisitos de Renovación de Licencia — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0021', 'v2026.3', 'active', 'bulk_veh_0021'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 1 (demo, bulk_veh_0021)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0021'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Tarifario de Trámites Vehiculares — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0022', 'v2026.3', 'active', 'bulk_veh_0022'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 1 (demo, bulk_veh_0022)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0022'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 2 (demo, bulk_veh_0022)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0022'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Consulta de Adeudos y Refrendo — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0023', 'v2026.3', 'active', 'bulk_veh_0023'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 1 (demo, bulk_veh_0023)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 2 (demo, bulk_veh_0023)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 3 (demo, bulk_veh_0023)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0023'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Módulos de Atención Vehicular — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0024', 'v2026.3', 'active', 'bulk_veh_0024'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 1 (demo, bulk_veh_0024)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0024'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'vehiculos', 'Cita Previa Vehicular — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0025', 'v2026.3', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_veh_0025'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 1 (demo, bulk_veh_0025)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0025'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 2 (demo, bulk_veh_0025)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0025'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Reposición de Placas y Tarjeta — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0026', 'v2026.3', 'active', 'bulk_veh_0026'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 1 (demo, bulk_veh_0026)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 2 (demo, bulk_veh_0026)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 3 (demo, bulk_veh_0026)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0026'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Verificación Vehicular Ambiental — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0027', 'v2026.3', 'active', 'bulk_veh_0027'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 1 (demo, bulk_veh_0027)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0027'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Licencias para Motociclista — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0028', 'v2026.3', 'active', 'bulk_veh_0028'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 1 (demo, bulk_veh_0028)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0028'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 2 (demo, bulk_veh_0028)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0028'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Descuentos por Pronto Pago — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0029', 'v2026.3', 'active', 'bulk_veh_0029'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 1 (demo, bulk_veh_0029)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 2 (demo, bulk_veh_0029)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 3 (demo, bulk_veh_0029)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0029'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Trámite de Baja Vehicular — variante 3 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0030', 'v2026.3', 'active', 'bulk_veh_0030'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 1 (demo, bulk_veh_0030)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0030'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Requisitos de Renovación de Licencia — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0031', 'v2026.4', 'active', 'bulk_veh_0031'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 1 (demo, bulk_veh_0031)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0031'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Renovación de Licencia — documento 2 (demo, bulk_veh_0031)',
  'Contenido de demostración. Para renovar la licencia de conducir se presenta identificacion oficial vigente, comprobante de domicilio reciente, la licencia anterior y el comprobante de pago de derechos. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0031'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Tarifario de Trámites Vehiculares — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0032', 'v2026.4', 'active', 'bulk_veh_0032'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 1 (demo, bulk_veh_0032)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 2 (demo, bulk_veh_0032)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario de Trámites Vehiculares — documento 3 (demo, bulk_veh_0032)',
  'Contenido de demostración. Las tarifas ilustrativas cubren renovacion, expedicion por primera vez y refrendo anual de control vehicular; los montos son de demostracion y no representan tarifas oficiales. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0032'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'vehiculos', 'Consulta de Adeudos y Refrendo — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0033', 'v2026.4', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_veh_0033'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Adeudos y Refrendo — documento 1 (demo, bulk_veh_0033)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de placa o de serie; el sistema muestra refrendos pendientes y multas asociadas. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0033'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Módulos de Atención Vehicular — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0034', 'v2026.4', 'active', 'bulk_veh_0034'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 1 (demo, bulk_veh_0034)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0034'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Atención Vehicular — documento 2 (demo, bulk_veh_0034)',
  'Contenido de demostración. Los modulos de atencion operan con distinta cobertura y reciben renovaciones, refrendos y reposiciones de tarjeta de circulacion. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0034'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Cita Previa Vehicular — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0035', 'v2026.4', 'active', 'bulk_veh_0035'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 1 (demo, bulk_veh_0035)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 2 (demo, bulk_veh_0035)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular — documento 3 (demo, bulk_veh_0035)',
  'Contenido de demostración. Se recomienda agendar cita previa para reducir el tiempo de espera; la reserva es idempotente y confirmar dos veces no duplica la cita. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0035'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Reposición de Placas y Tarjeta — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0036', 'v2026.4', 'active', 'bulk_veh_0036'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Reposición de Placas y Tarjeta — documento 1 (demo, bulk_veh_0036)',
  'Contenido de demostración. La reposicion por robo o extravio requiere denuncia o reporte y el comprobante de pago; el tramite es presencial en un modulo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0036'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Verificación Vehicular Ambiental — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0037', 'v2026.4', 'active', 'bulk_veh_0037'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 1 (demo, bulk_veh_0037)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0037'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Verificación Vehicular Ambiental — documento 2 (demo, bulk_veh_0037)',
  'Contenido de demostración. El calendario de verificacion se organiza por terminacion de placa; el resultado se registra en el historial del vehiculo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0037'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Licencias para Motociclista — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0038', 'v2026.4', 'active', 'bulk_veh_0038'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 1 (demo, bulk_veh_0038)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 2 (demo, bulk_veh_0038)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencias para Motociclista — documento 3 (demo, bulk_veh_0038)',
  'Contenido de demostración. La licencia de motociclista contempla vigencias diferenciadas y puede requerir evaluacion practica adicional segun el tipo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0038'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Descuentos por Pronto Pago — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0039', 'v2026.4', 'active', 'bulk_veh_0039'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago — documento 1 (demo, bulk_veh_0039)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por pronto pago del refrendo, decrecientes durante el primer trimestre del anio. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0039'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Trámite de Baja Vehicular — variante 4 (demostración)',
  'Instituto de Control Vehicular de Durango (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/veh-0040', 'v2026.4', 'active', 'bulk_veh_0040'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 1 (demo, bulk_veh_0040)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0040'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Trámite de Baja Vehicular — documento 2 (demo, bulk_veh_0040)',
  'Contenido de demostración. La baja vehicular exige la documentacion del vehiculo y la acreditacion del propietario; libera obligaciones de refrendo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_veh_0040'
on conflict (source_id, title) do nothing;
-- =========================================================================
-- AYUNTAMIENTO_EMPRESAS — 40 fuentes (namespace bulk_emp_*)
-- =========================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Dictamen de Uso de Suelo — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0001', 'v2026.1', 'active', 'bulk_emp_0001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 1 (demo, bulk_emp_0001)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 2 (demo, bulk_emp_0001)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Protección Civil para Negocios — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0002', 'v2026.1', 'active', 'bulk_emp_0002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 1 (demo, bulk_emp_0002)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 2 (demo, bulk_emp_0002)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 3 (demo, bulk_emp_0002)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Aviso de Funcionamiento Sanitario — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0003', 'v2026.1', 'active', 'bulk_emp_0003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 1 (demo, bulk_emp_0003)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Sistema de Apertura Rápida (SDARE) — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0004', 'v2026.1', 'active', 'bulk_emp_0004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 1 (demo, bulk_emp_0004)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 2 (demo, bulk_emp_0004)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0004'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Costos Municipales de Apertura — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0005', 'v2026.1', 'active', 'bulk_emp_0005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 1 (demo, bulk_emp_0005)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 2 (demo, bulk_emp_0005)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 3 (demo, bulk_emp_0005)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0005'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Licencia de Anuncios y Publicidad — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0006', 'v2026.1', 'active', 'bulk_emp_0006'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 1 (demo, bulk_emp_0006)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0006'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Giros con Venta de Alcohol — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0007', 'v2026.1', 'active', 'bulk_emp_0007'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 1 (demo, bulk_emp_0007)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0007'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 2 (demo, bulk_emp_0007)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0007'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Refrendo Anual de Licencia — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0008', 'v2026.1', 'active', 'bulk_emp_0008'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 1 (demo, bulk_emp_0008)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 2 (demo, bulk_emp_0008)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 3 (demo, bulk_emp_0008)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0008'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ayuntamiento_empresas', 'Inspección y Verificación de Giros — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0009', 'v2026.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_emp_0009'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 1 (demo, bulk_emp_0009)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0009'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Ventanilla Única Empresarial — variante 1 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0010', 'v2026.1', 'active', 'bulk_emp_0010'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 1 (demo, bulk_emp_0010)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0010'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 2 (demo, bulk_emp_0010)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0010'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Dictamen de Uso de Suelo — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0011', 'v2026.2', 'active', 'bulk_emp_0011'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 1 (demo, bulk_emp_0011)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 2 (demo, bulk_emp_0011)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 3 (demo, bulk_emp_0011)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0011'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Protección Civil para Negocios — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0012', 'v2026.2', 'active', 'bulk_emp_0012'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 1 (demo, bulk_emp_0012)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0012'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Aviso de Funcionamiento Sanitario — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0013', 'v2026.2', 'active', 'bulk_emp_0013'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 1 (demo, bulk_emp_0013)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0013'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 2 (demo, bulk_emp_0013)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0013'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Sistema de Apertura Rápida (SDARE) — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0014', 'v2026.2', 'active', 'bulk_emp_0014'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 1 (demo, bulk_emp_0014)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 2 (demo, bulk_emp_0014)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 3 (demo, bulk_emp_0014)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0014'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Costos Municipales de Apertura — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0015', 'v2026.2', 'active', 'bulk_emp_0015'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 1 (demo, bulk_emp_0015)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0015'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Licencia de Anuncios y Publicidad — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0016', 'v2026.2', 'active', 'bulk_emp_0016'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 1 (demo, bulk_emp_0016)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0016'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 2 (demo, bulk_emp_0016)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0016'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ayuntamiento_empresas', 'Giros con Venta de Alcohol — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0017', 'v2026.2', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_emp_0017'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 1 (demo, bulk_emp_0017)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 2 (demo, bulk_emp_0017)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 3 (demo, bulk_emp_0017)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0017'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Refrendo Anual de Licencia — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0018', 'v2026.2', 'active', 'bulk_emp_0018'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 1 (demo, bulk_emp_0018)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0018'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Inspección y Verificación de Giros — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0019', 'v2026.2', 'active', 'bulk_emp_0019'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 1 (demo, bulk_emp_0019)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0019'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 2 (demo, bulk_emp_0019)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0019'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Ventanilla Única Empresarial — variante 2 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0020', 'v2026.2', 'active', 'bulk_emp_0020'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 1 (demo, bulk_emp_0020)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 2 (demo, bulk_emp_0020)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 3 (demo, bulk_emp_0020)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0020'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Dictamen de Uso de Suelo — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0021', 'v2026.3', 'active', 'bulk_emp_0021'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 1 (demo, bulk_emp_0021)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0021'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Protección Civil para Negocios — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0022', 'v2026.3', 'active', 'bulk_emp_0022'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 1 (demo, bulk_emp_0022)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0022'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 2 (demo, bulk_emp_0022)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0022'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Aviso de Funcionamiento Sanitario — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0023', 'v2026.3', 'active', 'bulk_emp_0023'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 1 (demo, bulk_emp_0023)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 2 (demo, bulk_emp_0023)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 3 (demo, bulk_emp_0023)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0023'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Sistema de Apertura Rápida (SDARE) — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0024', 'v2026.3', 'active', 'bulk_emp_0024'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 1 (demo, bulk_emp_0024)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0024'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ayuntamiento_empresas', 'Costos Municipales de Apertura — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0025', 'v2026.3', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_emp_0025'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 1 (demo, bulk_emp_0025)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0025'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 2 (demo, bulk_emp_0025)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0025'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Licencia de Anuncios y Publicidad — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0026', 'v2026.3', 'active', 'bulk_emp_0026'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 1 (demo, bulk_emp_0026)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 2 (demo, bulk_emp_0026)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 3 (demo, bulk_emp_0026)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0026'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Giros con Venta de Alcohol — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0027', 'v2026.3', 'active', 'bulk_emp_0027'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 1 (demo, bulk_emp_0027)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0027'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Refrendo Anual de Licencia — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0028', 'v2026.3', 'active', 'bulk_emp_0028'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 1 (demo, bulk_emp_0028)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0028'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 2 (demo, bulk_emp_0028)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0028'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Inspección y Verificación de Giros — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0029', 'v2026.3', 'active', 'bulk_emp_0029'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 1 (demo, bulk_emp_0029)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 2 (demo, bulk_emp_0029)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 3 (demo, bulk_emp_0029)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0029'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Ventanilla Única Empresarial — variante 3 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0030', 'v2026.3', 'active', 'bulk_emp_0030'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 1 (demo, bulk_emp_0030)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0030'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Dictamen de Uso de Suelo — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0031', 'v2026.4', 'active', 'bulk_emp_0031'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 1 (demo, bulk_emp_0031)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0031'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Dictamen de Uso de Suelo — documento 2 (demo, bulk_emp_0031)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo indispensable para la licencia de funcionamiento y verifica si el giro esta permitido en el domicilio. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0031'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Protección Civil para Negocios — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0032', 'v2026.4', 'active', 'bulk_emp_0032'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 1 (demo, bulk_emp_0032)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 2 (demo, bulk_emp_0032)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Protección Civil para Negocios — documento 3 (demo, bulk_emp_0032)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno de proteccion civil: extintores vigentes, senializacion y salidas de emergencia. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0032'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ayuntamiento_empresas', 'Aviso de Funcionamiento Sanitario — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0033', 'v2026.4', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_emp_0033'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso de Funcionamiento Sanitario — documento 1 (demo, bulk_emp_0033)',
  'Contenido de demostración. Los establecimientos que manejan alimentos presentan aviso de funcionamiento sanitario y designan un responsable de higiene. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0033'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Sistema de Apertura Rápida (SDARE) — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0034', 'v2026.4', 'active', 'bulk_emp_0034'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 1 (demo, bulk_emp_0034)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0034'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Sistema de Apertura Rápida (SDARE) — documento 2 (demo, bulk_emp_0034)',
  'Contenido de demostración. El sistema de apertura rapida simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura en un mismo punto. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0034'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Costos Municipales de Apertura — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0035', 'v2026.4', 'active', 'bulk_emp_0035'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 1 (demo, bulk_emp_0035)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 2 (demo, bulk_emp_0035)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura — documento 3 (demo, bulk_emp_0035)',
  'Contenido de demostración. Los costos de la licencia de funcionamiento se determinan conforme a la ley de ingresos vigente de demo, segun giro y nivel de riesgo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0035'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Licencia de Anuncios y Publicidad — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0036', 'v2026.4', 'active', 'bulk_emp_0036'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Licencia de Anuncios y Publicidad — documento 1 (demo, bulk_emp_0036)',
  'Contenido de demostración. La colocacion de anuncios en fachada requiere licencia especifica que evalua dimensiones, seguridad estructural e imagen urbana. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0036'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Giros con Venta de Alcohol — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0037', 'v2026.4', 'active', 'bulk_emp_0037'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 1 (demo, bulk_emp_0037)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0037'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Giros con Venta de Alcohol — documento 2 (demo, bulk_emp_0037)',
  'Contenido de demostración. La venta de bebidas alcoholicas exige anuencia adicional y horarios regulados; el giro se clasifica de mayor riesgo administrativo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0037'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Refrendo Anual de Licencia — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0038', 'v2026.4', 'active', 'bulk_emp_0038'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 1 (demo, bulk_emp_0038)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 2 (demo, bulk_emp_0038)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo Anual de Licencia — documento 3 (demo, bulk_emp_0038)',
  'Contenido de demostración. La licencia de funcionamiento se refrenda cada ejercicio presentando el pago correspondiente y datos actualizados del giro. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0038'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Inspección y Verificación de Giros — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0039', 'v2026.4', 'active', 'bulk_emp_0039'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Inspección y Verificación de Giros — documento 1 (demo, bulk_emp_0039)',
  'Contenido de demostración. La verificacion documental confirma que el establecimiento cumple las condiciones declaradas; no sustituye una inspeccion fisica. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0039'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Ventanilla Única Empresarial — variante 4 (demostración)',
  'Dirección de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/emp-0040', 'v2026.4', 'active', 'bulk_emp_0040'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 1 (demo, bulk_emp_0040)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0040'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla Única Empresarial — documento 2 (demo, bulk_emp_0040)',
  'Contenido de demostración. La ventanilla unica concentra la orientacion sobre tramites de apertura y turna cada requisito a la dependencia competente. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_emp_0040'
on conflict (source_id, title) do nothing;
-- =========================================================================
-- REGISTRO_CIVIL — 40 fuentes (namespace bulk_rc_*)
-- =========================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Copias Certificadas de Actas — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0001', 'v2026.1', 'active', 'bulk_rc_0001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 1 (demo, bulk_rc_0001)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 2 (demo, bulk_rc_0001)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Aclaración de Actas — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0002', 'v2026.1', 'active', 'bulk_rc_0002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 1 (demo, bulk_rc_0002)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 2 (demo, bulk_rc_0002)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 3 (demo, bulk_rc_0002)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Corrección de Datos de Fondo — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0003', 'v2026.1', 'active', 'bulk_rc_0003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 1 (demo, bulk_rc_0003)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Directorio de Oficialías — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0004', 'v2026.1', 'active', 'bulk_rc_0004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 1 (demo, bulk_rc_0004)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 2 (demo, bulk_rc_0004)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0004'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Disponibilidad de Citas — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0005', 'v2026.1', 'active', 'bulk_rc_0005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 1 (demo, bulk_rc_0005)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 2 (demo, bulk_rc_0005)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 3 (demo, bulk_rc_0005)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0005'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Nacimiento — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0006', 'v2026.1', 'active', 'bulk_rc_0006'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 1 (demo, bulk_rc_0006)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0006'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Matrimonio — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0007', 'v2026.1', 'active', 'bulk_rc_0007'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 1 (demo, bulk_rc_0007)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0007'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 2 (demo, bulk_rc_0007)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0007'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Defunción — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0008', 'v2026.1', 'active', 'bulk_rc_0008'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 1 (demo, bulk_rc_0008)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 2 (demo, bulk_rc_0008)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 3 (demo, bulk_rc_0008)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0008'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'registro_civil', 'Registro Extemporáneo — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0009', 'v2026.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_rc_0009'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 1 (demo, bulk_rc_0009)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0009'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Constancias de Inexistencia — variante 1 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0010', 'v2026.1', 'active', 'bulk_rc_0010'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 1 (demo, bulk_rc_0010)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0010'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 2 (demo, bulk_rc_0010)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0010'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Copias Certificadas de Actas — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0011', 'v2026.2', 'active', 'bulk_rc_0011'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 1 (demo, bulk_rc_0011)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 2 (demo, bulk_rc_0011)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 3 (demo, bulk_rc_0011)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0011'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Aclaración de Actas — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0012', 'v2026.2', 'active', 'bulk_rc_0012'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 1 (demo, bulk_rc_0012)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0012'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Corrección de Datos de Fondo — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0013', 'v2026.2', 'active', 'bulk_rc_0013'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 1 (demo, bulk_rc_0013)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0013'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 2 (demo, bulk_rc_0013)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0013'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Directorio de Oficialías — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0014', 'v2026.2', 'active', 'bulk_rc_0014'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 1 (demo, bulk_rc_0014)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 2 (demo, bulk_rc_0014)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 3 (demo, bulk_rc_0014)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0014'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Disponibilidad de Citas — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0015', 'v2026.2', 'active', 'bulk_rc_0015'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 1 (demo, bulk_rc_0015)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0015'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Nacimiento — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0016', 'v2026.2', 'active', 'bulk_rc_0016'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 1 (demo, bulk_rc_0016)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0016'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 2 (demo, bulk_rc_0016)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0016'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'registro_civil', 'Acta de Matrimonio — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0017', 'v2026.2', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_rc_0017'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 1 (demo, bulk_rc_0017)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 2 (demo, bulk_rc_0017)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 3 (demo, bulk_rc_0017)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0017'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Defunción — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0018', 'v2026.2', 'active', 'bulk_rc_0018'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 1 (demo, bulk_rc_0018)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0018'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Registro Extemporáneo — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0019', 'v2026.2', 'active', 'bulk_rc_0019'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 1 (demo, bulk_rc_0019)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0019'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 2 (demo, bulk_rc_0019)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0019'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Constancias de Inexistencia — variante 2 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0020', 'v2026.2', 'active', 'bulk_rc_0020'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 1 (demo, bulk_rc_0020)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 2 (demo, bulk_rc_0020)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 3 (demo, bulk_rc_0020)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0020'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Copias Certificadas de Actas — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0021', 'v2026.3', 'active', 'bulk_rc_0021'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 1 (demo, bulk_rc_0021)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0021'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Aclaración de Actas — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0022', 'v2026.3', 'active', 'bulk_rc_0022'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 1 (demo, bulk_rc_0022)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0022'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 2 (demo, bulk_rc_0022)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0022'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Corrección de Datos de Fondo — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0023', 'v2026.3', 'active', 'bulk_rc_0023'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 1 (demo, bulk_rc_0023)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 2 (demo, bulk_rc_0023)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 3 (demo, bulk_rc_0023)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0023'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Directorio de Oficialías — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0024', 'v2026.3', 'active', 'bulk_rc_0024'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 1 (demo, bulk_rc_0024)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0024'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'registro_civil', 'Disponibilidad de Citas — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0025', 'v2026.3', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_rc_0025'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 1 (demo, bulk_rc_0025)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0025'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 2 (demo, bulk_rc_0025)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0025'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Nacimiento — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0026', 'v2026.3', 'active', 'bulk_rc_0026'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 1 (demo, bulk_rc_0026)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 2 (demo, bulk_rc_0026)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 3 (demo, bulk_rc_0026)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0026'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Matrimonio — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0027', 'v2026.3', 'active', 'bulk_rc_0027'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 1 (demo, bulk_rc_0027)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0027'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Defunción — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0028', 'v2026.3', 'active', 'bulk_rc_0028'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 1 (demo, bulk_rc_0028)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0028'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 2 (demo, bulk_rc_0028)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0028'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Registro Extemporáneo — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0029', 'v2026.3', 'active', 'bulk_rc_0029'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 1 (demo, bulk_rc_0029)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 2 (demo, bulk_rc_0029)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 3 (demo, bulk_rc_0029)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0029'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Constancias de Inexistencia — variante 3 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0030', 'v2026.3', 'active', 'bulk_rc_0030'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 1 (demo, bulk_rc_0030)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0030'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Copias Certificadas de Actas — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0031', 'v2026.4', 'active', 'bulk_rc_0031'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 1 (demo, bulk_rc_0031)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0031'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copias Certificadas de Actas — documento 2 (demo, bulk_rc_0031)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma presencial en una oficialia con identificacion oficial y los datos registrales. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0031'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Aclaración de Actas — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0032', 'v2026.4', 'active', 'bulk_rc_0032'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 1 (demo, bulk_rc_0032)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 2 (demo, bulk_rc_0032)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaración de Actas — documento 3 (demo, bulk_rc_0032)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se resuelve por aclaracion administrativa sin modificar el fondo del registro. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0032'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'registro_civil', 'Corrección de Datos de Fondo — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0033', 'v2026.4', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_rc_0033'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Corrección de Datos de Fondo — documento 1 (demo, bulk_rc_0033)',
  'Contenido de demostración. Cambiar un dato de fondo como apellido o fecha se tramita como correccion y puede requerir revision de la oficialia. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0033'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Directorio de Oficialías — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0034', 'v2026.4', 'active', 'bulk_rc_0034'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 1 (demo, bulk_rc_0034)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0034'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Oficialías — documento 2 (demo, bulk_rc_0034)',
  'Contenido de demostración. El directorio lista oficialias por zona; cada una atiende copias, aclaraciones y correcciones dentro de su circunscripcion. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0034'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Disponibilidad de Citas — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0035', 'v2026.4', 'active', 'bulk_rc_0035'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 1 (demo, bulk_rc_0035)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 2 (demo, bulk_rc_0035)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Disponibilidad de Citas — documento 3 (demo, bulk_rc_0035)',
  'Contenido de demostración. La disponibilidad de citas se consulta por oficialia y tipo de tramite; el sistema muestra horarios libres y permite reservar. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0035'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Nacimiento — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0036', 'v2026.4', 'active', 'bulk_rc_0036'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Nacimiento — documento 1 (demo, bulk_rc_0036)',
  'Contenido de demostración. El acta de nacimiento se emite con los datos del registro original; la copia certificada tiene la misma validez que el asiento. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0036'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Matrimonio — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0037', 'v2026.4', 'active', 'bulk_rc_0037'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 1 (demo, bulk_rc_0037)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0037'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Matrimonio — documento 2 (demo, bulk_rc_0037)',
  'Contenido de demostración. La copia certificada del acta de matrimonio requiere los datos de la partida y una identificacion de la persona solicitante. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0037'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Acta de Defunción — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0038', 'v2026.4', 'active', 'bulk_rc_0038'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 1 (demo, bulk_rc_0038)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 2 (demo, bulk_rc_0038)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Acta de Defunción — documento 3 (demo, bulk_rc_0038)',
  'Contenido de demostración. La copia certificada del acta de defuncion se solicita con los datos registrales; sirve para tramites sucesorios y administrativos. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0038'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Registro Extemporáneo — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0039', 'v2026.4', 'active', 'bulk_rc_0039'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro Extemporáneo — documento 1 (demo, bulk_rc_0039)',
  'Contenido de demostración. El registro extemporaneo aplica cuando el asiento se realiza fuera del plazo ordinario y puede requerir documentacion de respaldo. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0039'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Constancias de Inexistencia — variante 4 (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/rc-0040', 'v2026.4', 'active', 'bulk_rc_0040'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 1 (demo, bulk_rc_0040)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0040'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancias de Inexistencia — documento 2 (demo, bulk_rc_0040)',
  'Contenido de demostración. La constancia de inexistencia acredita que no obra un registro determinado y se emite tras la busqueda en el archivo. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_rc_0040'
on conflict (source_id, title) do nothing;
-- =========================================================================
-- SALUD — 40 fuentes (namespace bulk_sal_*)
-- =========================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Directorio de Unidades de Salud — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0001', 'v2026.1', 'active', 'bulk_sal_0001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 1 (demo, bulk_sal_0001)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 2 (demo, bulk_sal_0001)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Catálogo de Servicios Administrativos — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0002', 'v2026.1', 'active', 'bulk_sal_0002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 1 (demo, bulk_sal_0002)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 2 (demo, bulk_sal_0002)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 3 (demo, bulk_sal_0002)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Afiliación y Vigencia de Derechohabiencia — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0003', 'v2026.1', 'active', 'bulk_sal_0003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 1 (demo, bulk_sal_0003)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Horarios de Atención — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0004', 'v2026.1', 'active', 'bulk_sal_0004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 1 (demo, bulk_sal_0004)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 2 (demo, bulk_sal_0004)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0004'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Requisitos Documentales — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0005', 'v2026.1', 'active', 'bulk_sal_0005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 1 (demo, bulk_sal_0005)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 2 (demo, bulk_sal_0005)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 3 (demo, bulk_sal_0005)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0005'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Límite del Servicio de Orientación — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0006', 'v2026.1', 'active', 'bulk_sal_0006'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 1 (demo, bulk_sal_0006)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0006'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Ventanilla de Citas Administrativas — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0007', 'v2026.1', 'active', 'bulk_sal_0007'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 1 (demo, bulk_sal_0007)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0007'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 2 (demo, bulk_sal_0007)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0007'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Traslado entre Unidades — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0008', 'v2026.1', 'active', 'bulk_sal_0008'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 1 (demo, bulk_sal_0008)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 2 (demo, bulk_sal_0008)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 3 (demo, bulk_sal_0008)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0008'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'salud', 'Módulos de Afiliación — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0009', 'v2026.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_sal_0009'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 1 (demo, bulk_sal_0009)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0009'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Constancia de Vigencia de Derechos — variante 1 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0010', 'v2026.1', 'active', 'bulk_sal_0010'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 1 (demo, bulk_sal_0010)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0010'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 2 (demo, bulk_sal_0010)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0010'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Directorio de Unidades de Salud — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0011', 'v2026.2', 'active', 'bulk_sal_0011'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 1 (demo, bulk_sal_0011)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 2 (demo, bulk_sal_0011)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 3 (demo, bulk_sal_0011)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0011'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Catálogo de Servicios Administrativos — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0012', 'v2026.2', 'active', 'bulk_sal_0012'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 1 (demo, bulk_sal_0012)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0012'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Afiliación y Vigencia de Derechohabiencia — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0013', 'v2026.2', 'active', 'bulk_sal_0013'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 1 (demo, bulk_sal_0013)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0013'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 2 (demo, bulk_sal_0013)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0013'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Horarios de Atención — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0014', 'v2026.2', 'active', 'bulk_sal_0014'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 1 (demo, bulk_sal_0014)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 2 (demo, bulk_sal_0014)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 3 (demo, bulk_sal_0014)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0014'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Requisitos Documentales — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0015', 'v2026.2', 'active', 'bulk_sal_0015'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 1 (demo, bulk_sal_0015)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0015'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Límite del Servicio de Orientación — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0016', 'v2026.2', 'active', 'bulk_sal_0016'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 1 (demo, bulk_sal_0016)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0016'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 2 (demo, bulk_sal_0016)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0016'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'salud', 'Ventanilla de Citas Administrativas — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0017', 'v2026.2', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_sal_0017'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 1 (demo, bulk_sal_0017)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 2 (demo, bulk_sal_0017)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 3 (demo, bulk_sal_0017)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0017'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Traslado entre Unidades — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0018', 'v2026.2', 'active', 'bulk_sal_0018'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 1 (demo, bulk_sal_0018)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0018'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Módulos de Afiliación — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0019', 'v2026.2', 'active', 'bulk_sal_0019'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 1 (demo, bulk_sal_0019)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0019'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 2 (demo, bulk_sal_0019)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0019'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Constancia de Vigencia de Derechos — variante 2 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0020', 'v2026.2', 'active', 'bulk_sal_0020'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 1 (demo, bulk_sal_0020)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 2 (demo, bulk_sal_0020)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 3 (demo, bulk_sal_0020)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0020'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Directorio de Unidades de Salud — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0021', 'v2026.3', 'active', 'bulk_sal_0021'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 1 (demo, bulk_sal_0021)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0021'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Catálogo de Servicios Administrativos — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0022', 'v2026.3', 'active', 'bulk_sal_0022'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 1 (demo, bulk_sal_0022)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0022'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 2 (demo, bulk_sal_0022)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0022'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Afiliación y Vigencia de Derechohabiencia — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0023', 'v2026.3', 'active', 'bulk_sal_0023'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 1 (demo, bulk_sal_0023)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 2 (demo, bulk_sal_0023)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 3 (demo, bulk_sal_0023)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0023'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Horarios de Atención — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0024', 'v2026.3', 'active', 'bulk_sal_0024'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 1 (demo, bulk_sal_0024)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0024'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'salud', 'Requisitos Documentales — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0025', 'v2026.3', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_sal_0025'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 1 (demo, bulk_sal_0025)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0025'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 2 (demo, bulk_sal_0025)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0025'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Límite del Servicio de Orientación — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0026', 'v2026.3', 'active', 'bulk_sal_0026'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 1 (demo, bulk_sal_0026)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 2 (demo, bulk_sal_0026)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 3 (demo, bulk_sal_0026)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0026'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Ventanilla de Citas Administrativas — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0027', 'v2026.3', 'active', 'bulk_sal_0027'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 1 (demo, bulk_sal_0027)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0027'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Traslado entre Unidades — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0028', 'v2026.3', 'active', 'bulk_sal_0028'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 1 (demo, bulk_sal_0028)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0028'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 2 (demo, bulk_sal_0028)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0028'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Módulos de Afiliación — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0029', 'v2026.3', 'active', 'bulk_sal_0029'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 1 (demo, bulk_sal_0029)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 2 (demo, bulk_sal_0029)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 3 (demo, bulk_sal_0029)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0029'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Constancia de Vigencia de Derechos — variante 3 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0030', 'v2026.3', 'active', 'bulk_sal_0030'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 1 (demo, bulk_sal_0030)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0030'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Directorio de Unidades de Salud — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0031', 'v2026.4', 'active', 'bulk_sal_0031'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 1 (demo, bulk_sal_0031)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0031'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades de Salud — documento 2 (demo, bulk_sal_0031)',
  'Contenido de demostración. La unidad aplicable depende del municipio y la afiliacion; el directorio orienta a que unidad acudir de forma administrativa. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0031'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Catálogo de Servicios Administrativos — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0032', 'v2026.4', 'active', 'bulk_sal_0032'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 1 (demo, bulk_sal_0032)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 2 (demo, bulk_sal_0032)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Catálogo de Servicios Administrativos — documento 3 (demo, bulk_sal_0032)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como agenda de citas y ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0032'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'salud', 'Afiliación y Vigencia de Derechohabiencia — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0033', 'v2026.4', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_sal_0033'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Afiliación y Vigencia de Derechohabiencia — documento 1 (demo, bulk_sal_0033)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la unidad o en el portal de demo y sirve para conocer la unidad asignada. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0033'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Horarios de Atención — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0034', 'v2026.4', 'active', 'bulk_sal_0034'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 1 (demo, bulk_sal_0034)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0034'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atención — documento 2 (demo, bulk_sal_0034)',
  'Contenido de demostración. Las unidades atienden en horario matutino y vespertino; la informacion es unicamente administrativa y de ubicacion. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0034'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Requisitos Documentales — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0035', 'v2026.4', 'active', 'bulk_sal_0035'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 1 (demo, bulk_sal_0035)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 2 (demo, bulk_sal_0035)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales — documento 3 (demo, bulk_sal_0035)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse identificacion oficial y, en su caso, comprobante de afiliacion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0035'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Límite del Servicio de Orientación — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0036', 'v2026.4', 'active', 'bulk_sal_0036'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Límite del Servicio de Orientación — documento 1 (demo, bulk_sal_0036)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, servicios, requisitos y horarios; ante una urgencia se indica acudir al 911. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0036'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Ventanilla de Citas Administrativas — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0037', 'v2026.4', 'active', 'bulk_sal_0037'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 1 (demo, bulk_sal_0037)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0037'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ventanilla de Citas Administrativas — documento 2 (demo, bulk_sal_0037)',
  'Contenido de demostración. La ventanilla gestiona el registro y la reprogramacion de citas de primer contacto de manera puramente administrativa. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0037'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Traslado entre Unidades — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0038', 'v2026.4', 'active', 'bulk_sal_0038'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 1 (demo, bulk_sal_0038)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 2 (demo, bulk_sal_0038)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Traslado entre Unidades — documento 3 (demo, bulk_sal_0038)',
  'Contenido de demostración. El cambio de unidad asignada es un tramite administrativo que actualiza el registro de adscripcion de la persona. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0038'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Módulos de Afiliación — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0039', 'v2026.4', 'active', 'bulk_sal_0039'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Módulos de Afiliación — documento 1 (demo, bulk_sal_0039)',
  'Contenido de demostración. Los modulos de afiliacion reciben altas y actualizaciones de datos de derechohabiencia dentro de su cobertura territorial. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0039'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Constancia de Vigencia de Derechos — variante 4 (demostración)',
  'Secretaría de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/sal-0040', 'v2026.4', 'active', 'bulk_sal_0040'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 1 (demo, bulk_sal_0040)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0040'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Vigencia de Derechos — documento 2 (demo, bulk_sal_0040)',
  'Contenido de demostración. La constancia de vigencia acredita administrativamente la afiliacion y se descarga o se solicita en ventanilla. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_sal_0040'
on conflict (source_id, title) do nothing;
-- =========================================================================
-- GANADERIA — 40 fuentes (namespace bulk_gan_*)
-- =========================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Expediente e Historial Animal — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0001', 'v2026.1', 'active', 'bulk_gan_0001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 1 (demo, bulk_gan_0001)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 2 (demo, bulk_gan_0001)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Vacunación — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0002', 'v2026.1', 'active', 'bulk_gan_0002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 1 (demo, bulk_gan_0002)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 2 (demo, bulk_gan_0002)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 3 (demo, bulk_gan_0002)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Requisitos de Movilización Pecuaria — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0003', 'v2026.1', 'active', 'bulk_gan_0003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 1 (demo, bulk_gan_0003)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Alertas Sanitarias y Zonas de Restricción — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0004', 'v2026.1', 'active', 'bulk_gan_0004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 1 (demo, bulk_gan_0004)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 2 (demo, bulk_gan_0004)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0004'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Calendario de Vacunación Recomendado — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0005', 'v2026.1', 'active', 'bulk_gan_0005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 1 (demo, bulk_gan_0005)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 2 (demo, bulk_gan_0005)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0005'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 3 (demo, bulk_gan_0005)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0005'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Constancia de Hato — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0006', 'v2026.1', 'active', 'bulk_gan_0006'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 1 (demo, bulk_gan_0006)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0006'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Aretado e Identificación — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0007', 'v2026.1', 'active', 'bulk_gan_0007'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 1 (demo, bulk_gan_0007)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0007'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 2 (demo, bulk_gan_0007)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0007'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Guía de Tránsito Interno — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0008', 'v2026.1', 'active', 'bulk_gan_0008'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 1 (demo, bulk_gan_0008)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 2 (demo, bulk_gan_0008)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0008'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 3 (demo, bulk_gan_0008)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0008'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ganaderia', 'Registro de Unidades de Producción — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0009', 'v2026.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_gan_0009'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 1 (demo, bulk_gan_0009)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0009'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Control de Eventos Sanitarios — variante 1 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0010', 'v2026.1', 'active', 'bulk_gan_0010'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 1 (demo, bulk_gan_0010)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0010'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 2 (demo, bulk_gan_0010)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0010'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Expediente e Historial Animal — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0011', 'v2026.2', 'active', 'bulk_gan_0011'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 1 (demo, bulk_gan_0011)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 2 (demo, bulk_gan_0011)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0011'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 3 (demo, bulk_gan_0011)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0011'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Vacunación — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0012', 'v2026.2', 'active', 'bulk_gan_0012'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 1 (demo, bulk_gan_0012)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0012'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Requisitos de Movilización Pecuaria — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0013', 'v2026.2', 'active', 'bulk_gan_0013'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 1 (demo, bulk_gan_0013)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0013'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 2 (demo, bulk_gan_0013)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0013'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Alertas Sanitarias y Zonas de Restricción — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0014', 'v2026.2', 'active', 'bulk_gan_0014'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 1 (demo, bulk_gan_0014)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 2 (demo, bulk_gan_0014)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0014'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 3 (demo, bulk_gan_0014)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0014'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Calendario de Vacunación Recomendado — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0015', 'v2026.2', 'active', 'bulk_gan_0015'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 1 (demo, bulk_gan_0015)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0015'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Constancia de Hato — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0016', 'v2026.2', 'active', 'bulk_gan_0016'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 1 (demo, bulk_gan_0016)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0016'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 2 (demo, bulk_gan_0016)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0016'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ganaderia', 'Aretado e Identificación — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0017', 'v2026.2', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_gan_0017'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 1 (demo, bulk_gan_0017)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 2 (demo, bulk_gan_0017)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0017'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 3 (demo, bulk_gan_0017)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0017'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Guía de Tránsito Interno — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0018', 'v2026.2', 'active', 'bulk_gan_0018'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 1 (demo, bulk_gan_0018)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0018'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Unidades de Producción — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0019', 'v2026.2', 'active', 'bulk_gan_0019'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 1 (demo, bulk_gan_0019)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0019'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 2 (demo, bulk_gan_0019)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0019'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Control de Eventos Sanitarios — variante 2 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0020', 'v2026.2', 'active', 'bulk_gan_0020'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 1 (demo, bulk_gan_0020)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 2 (demo, bulk_gan_0020)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0020'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 3 (demo, bulk_gan_0020)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0020'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Expediente e Historial Animal — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0021', 'v2026.3', 'active', 'bulk_gan_0021'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 1 (demo, bulk_gan_0021)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0021'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Vacunación — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0022', 'v2026.3', 'active', 'bulk_gan_0022'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 1 (demo, bulk_gan_0022)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0022'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 2 (demo, bulk_gan_0022)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0022'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Requisitos de Movilización Pecuaria — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0023', 'v2026.3', 'active', 'bulk_gan_0023'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 1 (demo, bulk_gan_0023)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 2 (demo, bulk_gan_0023)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0023'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 3 (demo, bulk_gan_0023)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0023'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Alertas Sanitarias y Zonas de Restricción — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0024', 'v2026.3', 'active', 'bulk_gan_0024'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 1 (demo, bulk_gan_0024)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0024'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ganaderia', 'Calendario de Vacunación Recomendado — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0025', 'v2026.3', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'bulk_gan_0025'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 1 (demo, bulk_gan_0025)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0025'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 2 (demo, bulk_gan_0025)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0025'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Constancia de Hato — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0026', 'v2026.3', 'active', 'bulk_gan_0026'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 1 (demo, bulk_gan_0026)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 2 (demo, bulk_gan_0026)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0026'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 3 (demo, bulk_gan_0026)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0026'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Aretado e Identificación — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0027', 'v2026.3', 'active', 'bulk_gan_0027'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 1 (demo, bulk_gan_0027)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0027'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Guía de Tránsito Interno — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0028', 'v2026.3', 'active', 'bulk_gan_0028'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 1 (demo, bulk_gan_0028)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0028'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 2 (demo, bulk_gan_0028)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0028'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Unidades de Producción — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0029', 'v2026.3', 'active', 'bulk_gan_0029'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 1 (demo, bulk_gan_0029)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 2 (demo, bulk_gan_0029)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0029'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 3 (demo, bulk_gan_0029)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0029'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Control de Eventos Sanitarios — variante 3 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0030', 'v2026.3', 'active', 'bulk_gan_0030'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 1 (demo, bulk_gan_0030)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0030'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Expediente e Historial Animal — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0031', 'v2026.4', 'active', 'bulk_gan_0031'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 1 (demo, bulk_gan_0031)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0031'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Expediente e Historial Animal — documento 2 (demo, bulk_gan_0031)',
  'Contenido de demostración. El expediente animal se consulta mediante una referencia opaca (no el arete real) y muestra la ficha y el historial sanitario. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0031'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Vacunación — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0032', 'v2026.4', 'active', 'bulk_gan_0032'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 1 (demo, bulk_gan_0032)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 2 (demo, bulk_gan_0032)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0032'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Vacunación — documento 3 (demo, bulk_gan_0032)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y confirmacion expresa del productor; la operacion es idempotente y devuelve el mismo folio. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0032'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ganaderia', 'Requisitos de Movilización Pecuaria — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0033', 'v2026.4', 'expired',
  '2023-01-01T00:00:00Z', '2023-12-31T23:59:59Z', 'bulk_gan_0033'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilización Pecuaria — documento 1 (demo, bulk_gan_0033)',
  'Contenido de demostración. La validacion documental requiere referencia del animal, destino e historial; el resultado NO autoriza por si mismo la movilizacion. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0033'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Alertas Sanitarias y Zonas de Restricción — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0034', 'v2026.4', 'active', 'bulk_gan_0034'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 1 (demo, bulk_gan_0034)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en zona norte opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0034'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Alertas Sanitarias y Zonas de Restricción — documento 2 (demo, bulk_gan_0034)',
  'Contenido de demostración. Las alertas informan zonas con restriccion temporal de movilizacion por motivos sanitarios y se consultan antes de validar un traslado. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0034'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Calendario de Vacunación Recomendado — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0035', 'v2026.4', 'active', 'bulk_gan_0035'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 1 (demo, bulk_gan_0035)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en zona sur opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 2 (demo, bulk_gan_0035)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0035'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunación Recomendado — documento 3 (demo, bulk_gan_0035)',
  'Contenido de demostración. El calendario sugiere aplicaciones periodicas segun especie y edad; es una guia administrativa que no sustituye al medico veterinario. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0035'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Constancia de Hato — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0036', 'v2026.4', 'active', 'bulk_gan_0036'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Constancia de Hato — documento 1 (demo, bulk_gan_0036)',
  'Contenido de demostración. La constancia de hato describe la composicion declarada del predio con fines administrativos y de trazabilidad de demostracion. En el ejercicio de demo la atencion en zona oriente opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0036'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Aretado e Identificación — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0037', 'v2026.4', 'active', 'bulk_gan_0037'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 1 (demo, bulk_gan_0037)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en zona poniente opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0037'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aretado e Identificación — documento 2 (demo, bulk_gan_0037)',
  'Contenido de demostración. El aretado asigna una referencia opaca al animal para su seguimiento; la referencia no revela datos personales del productor. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven dentro de la misma semana. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0037'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Guía de Tránsito Interno — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0038', 'v2026.4', 'active', 'bulk_gan_0038'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 1 (demo, bulk_gan_0038)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en corredor industrial opera de lunes a sábado con horario ampliado, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 2 (demo, bulk_gan_0038)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0038'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guía de Tránsito Interno — documento 3 (demo, bulk_gan_0038)',
  'Contenido de demostración. La guia de transito interno documenta el desplazamiento entre predios de un mismo productor dentro de la misma circunscripcion. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0038'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Unidades de Producción — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0039', 'v2026.4', 'active', 'bulk_gan_0039'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Registro de Unidades de Producción — documento 1 (demo, bulk_gan_0039)',
  'Contenido de demostración. El registro de la unidad de produccion vincula el predio con su responsable declarado y habilita otros tramites pecuarios. En el ejercicio de demo la atencion en cabecera municipal opera de lunes a viernes en horario corrido, y los tramites relacionados se resuelven en pocos días hábiles. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0039'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Control de Eventos Sanitarios — variante 4 (demostración)',
  'Secretaría de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/gan-0040', 'v2026.4', 'active', 'bulk_gan_0040'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 1 (demo, bulk_gan_0040)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en distrito histórico opera de martes a sábado en horario vespertino, y los tramites relacionados se resuelven en un plazo estimado de 24 a 72 horas. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0040'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Control de Eventos Sanitarios — documento 2 (demo, bulk_gan_0040)',
  'Contenido de demostración. Cada evento sanitario se asienta con tipo, fecha y responsable en el historial del animal para su consulta posterior. En el ejercicio de demo la atencion en zona centro opera de lunes a viernes en horario matutino, y los tramites relacionados se resuelven en el transcurso del mes. Datos ilustrativos de demostracion; no representan un tramite oficial real ni reproducen documentos institucionales.'
from public.sources s where s.checksum = 'bulk_gan_0040'
on conflict (source_id, title) do nothing;

-- =============================================================================
-- CHUNKS — un chunk por documento, embedding fake determinista.
-- Cubre todos los documentos sembrados arriba (checksums bulk_*).
-- =============================================================================

insert into public.chunks (tenant_id, document_id, domain, chunk_index, content, embedding, checksum)
select d.tenant_id, d.id, s.domain, 0, d.content_raw,
  public.fake_embedding(d.content_raw), md5(d.content_raw)
from public.documents d
join public.sources s on s.id = d.source_id
where s.checksum like 'bulk\_%'
and d.content_raw is not null
on conflict (document_id, chunk_index) do nothing;
