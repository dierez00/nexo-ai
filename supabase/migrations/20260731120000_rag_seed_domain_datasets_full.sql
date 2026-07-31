-- =============================================================================
-- SaaS v1.3.0 — Seed RAG: datasets amplios por dominio (los 5 módulos)
-- =============================================================================
-- Completa el trabajo iniciado en
-- 20260504190000_rag_seed_vehiculos_salud_empresas.sql (que solo cubrió 3 de los
-- 5 dominios) sembrando datasets equilibrados para los CINCO dominios:
-- vehiculos, ayuntamiento_empresas, registro_civil, salud y ganaderia.
--
-- Contenido 100% SINTÉTICO de demostración (marcado "(demostración)" en cada
-- fuente, coherente con el encabezado sintético de domains/vehiculos/sources.yaml
-- y con la exclusión de domains/README.md: sin PII ni credenciales). No reproduce
-- documentos institucionales reales ni inventa cifras oficiales; las cantidades
-- son ilustrativas de demo.
--
-- Espacio de checksums propio `syn_<dom>_NNN` para NO colisionar con los hashes
-- reales del seed 20260504190000 (que su test verifica exactamente).
--
-- Idempotente por las constraints ya existentes:
--   sources_tenant_checksum_key (tenant_id, checksum)
--   documents_source_title_key  (source_id, title)
--   chunks_document_chunk_index_key (document_id, chunk_index)
-- Cada dominio incluye ≥1 fuente vencida/sustituida (status expired/superseded)
-- para ejercitar el filtrado por vigencia de public.match_chunks.
-- =============================================================================

-- =============================================================================
-- VEHÍCULOS — 5 fuentes (4 activas + 1 sustituida), 9 documentos
-- =============================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Requisitos de Renovación de Licencia (demostración)',
  'Instituto de Control Vehicular (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/renovacion', 'v2026.1', 'active', 'syn_veh_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Renovación de Licencia Tipo A — Requisitos (demo)',
  'Contenido de demostración. Para renovar la licencia de conducir tipo A se '
  'presenta: identificacion oficial vigente, comprobante de domicilio reciente, '
  'la licencia anterior o su reporte de extravio, y el comprobante de pago de '
  'derechos. El tramite es presencial en un modulo de atencion vehicular. Cifras '
  'y requisitos ilustrativos; no representan un tramite oficial real.'
from public.sources s where s.checksum = 'syn_veh_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Vigencias y Tipos de Licencia (demo)',
  'Contenido de demostración. Las licencias de demostracion contemplan vigencias '
  'de 3 o 6 anios para automovilista y motociclista. La renovacion se puede '
  'iniciar hasta 60 dias antes del vencimiento. Datos ilustrativos de demo.'
from public.sources s where s.checksum = 'syn_veh_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Tarifas de Tramites Vehiculares 2026 (demostración)',
  'Tesoreria Estatal (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/tarifas-2026', 'v2026.1', 'active', 'syn_veh_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario Vehicular 2026 (demo)',
  'Contenido de demostración. Tarifas ilustrativas 2026: renovacion de licencia, '
  'expedicion por primera vez y refrendo anual de control vehicular. Los montos '
  'son de demostracion y se definen conforme a la normativa vigente de demo.'
from public.sources s where s.checksum = 'syn_veh_002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Descuentos por Pronto Pago (demo)',
  'Contenido de demostración. En el ejercicio de demo se aplican descuentos por '
  'pronto pago del refrendo: mayor porcentaje en enero y decreciente hasta marzo. '
  'Porcentajes ilustrativos; vigencia del beneficio dentro del primer trimestre.'
from public.sources s where s.checksum = 'syn_veh_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Consulta de Adeudos y Refrendo (demostración)',
  'Instituto de Control Vehicular (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/adeudos', 'v2026.1', 'active', 'syn_veh_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Como Consultar Adeudos Vehiculares (demo)',
  'Contenido de demostración. El adeudo vehicular se consulta con el numero de '
  'placa o de serie en el portal de demostracion o en un modulo. El sistema '
  'muestra refrendos pendientes y, en su caso, multas asociadas. Flujo de demo.'
from public.sources s where s.checksum = 'syn_veh_003'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Refrendo y Tarjeta de Circulacion (demo)',
  'Contenido de demostración. El refrendo anual mantiene vigente la tarjeta de '
  'circulacion. En este entorno de demo la tenencia se considera subsidiada, por '
  'lo que solo se cubre el refrendo. Informacion ilustrativa de demostracion.'
from public.sources s where s.checksum = 'syn_veh_003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Modulos de Atencion Vehicular (demostración)',
  'Instituto de Control Vehicular (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/modulos', 'v2026.1', 'active', 'syn_veh_004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ubicacion y Horarios de Modulos (demo)',
  'Contenido de demostración. Los modulos de atencion de demo operan de lunes a '
  'viernes en horario de oficina y sabados con horario reducido. Se listan '
  'ubicaciones ficticias en zona centro y zona oriente. Datos de demostracion.'
from public.sources s where s.checksum = 'syn_veh_004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Cita Previa Vehicular (demo)',
  'Contenido de demostración. Se recomienda agendar cita previa para renovacion. '
  'La cita reserva un horario y reduce el tiempo de espera. En este entorno de '
  'demo la reserva es idempotente: confirmar dos veces no duplica la cita.'
from public.sources s where s.checksum = 'syn_veh_004'
on conflict (source_id, title) do nothing;

-- Fuente SUSTITUIDA: tarifas 2024 (caso de vigencia — no debe salir en retrieval activo)
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'vehiculos', 'Tarifas Vehiculares 2024 (sustituido, demostración)',
  'Tesoreria Estatal (demostración)',
  'https://demo.gobierno-demo.mx/vehiculos/tarifas-2024', 'v2024.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'syn_veh_005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario Vehicular 2024 (sustituido, demo)',
  'Contenido de demostración SUSTITUIDO. Tarifas del ejercicio 2024, conservadas '
  'como caso negativo de vigencia: usan casi las mismas palabras que el tarifario '
  '2026 pero NO deben aparecer en el retrieval activo. Datos de demostracion.'
from public.sources s where s.checksum = 'syn_veh_005'
on conflict (source_id, title) do nothing;

-- =============================================================================
-- AYUNTAMIENTO / EMPRESAS — 5 fuentes (4 activas + 1 vencida), 7 documentos
-- =============================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Dictamen de Uso de Suelo (demostración)',
  'Direccion de Desarrollo Urbano (demostración)',
  'https://demo.gobierno-demo.mx/empresas/uso-suelo', 'v2026.1', 'active', 'syn_emp_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Uso de Suelo — Requisito Previo (demo)',
  'Contenido de demostración. El dictamen de uso de suelo es el requisito previo '
  'indispensable para la licencia de funcionamiento. Verifica si el giro esta '
  'permitido en el domicilio. Se tramita antes de cualquier licencia. Flujo demo.'
from public.sources s where s.checksum = 'syn_emp_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Plazos de Uso de Suelo por Riesgo (demo)',
  'Contenido de demostración. Plazos ilustrativos: giros de bajo riesgo se '
  'resuelven en 24 horas; mediano riesgo y regulacion especial en algunos dias '
  'habiles. Tiempos de demostracion, no representan un tramite oficial real.'
from public.sources s where s.checksum = 'syn_emp_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Proteccion Civil para Negocios (demostración)',
  'Unidad Municipal de Proteccion Civil (demostración)',
  'https://demo.gobierno-demo.mx/empresas/proteccion-civil', 'v2026.1', 'active', 'syn_emp_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Visto Bueno de Proteccion Civil (demo)',
  'Contenido de demostración. Los giros de mediano riesgo requieren visto bueno '
  'de proteccion civil: extintores vigentes, senializacion y salidas de '
  'emergencia. Los de bajo riesgo suelen presentar autodeclaracion. Ejemplo demo.'
from public.sources s where s.checksum = 'syn_emp_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Aviso de Funcionamiento Sanitario (demostración)',
  'Regulacion Sanitaria (demostración)',
  'https://demo.gobierno-demo.mx/empresas/aviso-sanitario', 'v2026.1', 'active', 'syn_emp_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aviso Sanitario para Giros de Alimentos (demo)',
  'Contenido de demostración. Los establecimientos que manejan alimentos '
  'presentan aviso de funcionamiento sanitario y designan un responsable de '
  'higiene. Requisito complementario a la licencia municipal. Ejemplo de demo.'
from public.sources s where s.checksum = 'syn_emp_003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'SDARE — Apertura Rapida y Tarifas (demostración)',
  'Sistema de Apertura Rapida de Empresas (demostración)',
  'https://demo.gobierno-demo.mx/empresas/sdare', 'v2026.1', 'active', 'syn_emp_004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Que es el SDARE (demo)',
  'Contenido de demostración. El Sistema de Apertura Rapida de Empresas '
  'simplifica los tramites para negocios de bajo riesgo, resolviendo la apertura '
  'en pocos dias habiles y en un mismo punto de atencion. Descripcion de demo.'
from public.sources s where s.checksum = 'syn_emp_004'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costos Municipales de Apertura (demo)',
  'Contenido de demostración. Los costos de licencia de funcionamiento se '
  'determinan conforme a la ley de ingresos vigente de demo, segun el giro y el '
  'nivel de riesgo. Montos ilustrativos; no representan tarifas oficiales reales.'
from public.sources s where s.checksum = 'syn_emp_004'
on conflict (source_id, title) do nothing;

-- Fuente VENCIDA: tarifas municipales 2024 (caso de vigencia)
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ayuntamiento_empresas', 'Tarifas Municipales 2024 (vencido, demostración)',
  'Tesoreria Municipal (demostración)',
  'https://demo.gobierno-demo.mx/empresas/tarifas-2024', 'v2024.1', 'expired',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'syn_emp_005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Tarifario Municipal 2024 (vencido, demo)',
  'Contenido de demostración VENCIDO. Tarifas municipales del ejercicio 2024, '
  'conservadas como caso negativo de vigencia: no deben aparecer en el retrieval '
  'activo pese a su alta similitud lexica con las tarifas actuales. Datos demo.'
from public.sources s where s.checksum = 'syn_emp_005'
on conflict (source_id, title) do nothing;

-- =============================================================================
-- REGISTRO CIVIL — 5 fuentes (4 activas + 1 sustituida), 7 documentos
-- =============================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Copias Certificadas de Actas (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/copias', 'v2026.1', 'active', 'syn_rc_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Copia Certificada — Requisitos y Costo (demo)',
  'Contenido de demostración. La copia certificada de un acta se obtiene de forma '
  'presencial en una oficialia con una identificacion oficial y los datos '
  'registrales (nombre, fecha y lugar). Costo ilustrativo de demostracion.'
from public.sources s where s.checksum = 'syn_rc_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Actas Disponibles: Nacimiento, Matrimonio y Defuncion (demo)',
  'Contenido de demostración. En este entorno de demo se emiten copias '
  'certificadas de actas de nacimiento, matrimonio y defuncion. Cada tipo puede '
  'requerir datos especificos del registro. Informacion ilustrativa de demo.'
from public.sources s where s.checksum = 'syn_rc_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Aclaraciones y Correcciones de Actas (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/correcciones', 'v2026.1', 'active', 'syn_rc_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Aclaracion vs Correccion (demo)',
  'Contenido de demostración. Un error de ortografia, captura o transcripcion se '
  'resuelve por aclaracion administrativa. Cambiar un dato de fondo como apellido '
  'o fecha se tramita como correccion y puede requerir revision de la oficialia. '
  'Si solo se menciona un error a cambiar sin precisar, se pregunta el tipo.'
from public.sources s where s.checksum = 'syn_rc_002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos para Correccion de Fondo (demo)',
  'Contenido de demostración. La correccion de un dato de fondo requiere el acta '
  'a corregir, documentos que respalden el dato correcto e identificacion del '
  'solicitante. La resolucion queda sujeta a revision de la oficialia. Demo.'
from public.sources s where s.checksum = 'syn_rc_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Directorio de Oficialias (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/oficialias', 'v2026.1', 'active', 'syn_rc_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Oficialias y Horarios (demo)',
  'Contenido de demostración. El directorio de demo lista oficialias en zona '
  'centro y colonias, con horario de lunes a viernes. Cada oficialia atiende '
  'copias, aclaraciones y correcciones. Ubicaciones ficticias de demostracion.'
from public.sources s where s.checksum = 'syn_rc_003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'registro_civil', 'Disponibilidad de Citas en Oficialias (demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/disponibilidad', 'v2026.1', 'active', 'syn_rc_004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Disponibilidad (demo)',
  'Contenido de demostración. La disponibilidad de citas se consulta por '
  'oficialia y tipo de tramite. El sistema de demo muestra horarios libres y '
  'permite reservar un espacio. Flujo ilustrativo de demostracion.'
from public.sources s where s.checksum = 'syn_rc_004'
on conflict (source_id, title) do nothing;

-- Fuente SUSTITUIDA: guia de tramites 2024 (caso de vigencia)
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'registro_civil', 'Guia de Tramites de Actas 2024 (sustituida, demostración)',
  'Registro Civil (demostración)',
  'https://demo.gobierno-demo.mx/registro-civil/tramites-2024', 'v2024.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'syn_rc_005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Guia de Tramites de Actas 2024 (sustituida, demo)',
  'Contenido de demostración SUSTITUIDO. Guia del ejercicio 2024 conservada como '
  'caso negativo de vigencia: describe copias y correcciones con vocabulario casi '
  'identico al vigente pero NO debe aparecer en el retrieval activo. Datos demo.'
from public.sources s where s.checksum = 'syn_rc_005'
on conflict (source_id, title) do nothing;

-- =============================================================================
-- SALUD — 5 fuentes (4 activas + 1 vencida), 7 documentos
-- Solo NAVEGACION ADMINISTRATIVA (domains/salud/safety_policy.yaml): sin
-- diagnostico, receta ni interpretacion de sintomas.
-- =============================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Directorio de Unidades de Salud (demostración)',
  'Secretaria de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/directorio', 'v2026.1', 'active', 'syn_sal_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Unidades por Municipio y Afiliacion (demo)',
  'Contenido de demostración. La unidad de salud aplicable depende del municipio '
  'y de la afiliacion de la persona. El directorio de demo orienta a que unidad '
  'acudir de forma administrativa, sin brindar consejo clinico. Datos ficticios.'
from public.sources s where s.checksum = 'syn_sal_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Horarios de Atencion (demo)',
  'Contenido de demostración. Las unidades de demo atienden en horario matutino y '
  'vespertino; algunas cuentan con urgencias las 24 horas. Esta informacion es '
  'unicamente administrativa y de ubicacion. Horarios ilustrativos de demo.'
from public.sources s where s.checksum = 'syn_sal_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Catalogo de Servicios Administrativos (demostración)',
  'Secretaria de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/servicios', 'v2026.1', 'active', 'syn_sal_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Servicios Administrativos Disponibles (demo)',
  'Contenido de demostración. Se orienta sobre servicios administrativos como '
  'consulta de primer contacto, agenda de citas y ventanilla de afiliacion. No se '
  'ofrece diagnostico ni tratamiento. Catalogo ilustrativo de demostracion.'
from public.sources s where s.checksum = 'syn_sal_002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos y Documentacion (demo)',
  'Contenido de demostración. Para tramites administrativos suele solicitarse '
  'identificacion oficial y, en su caso, comprobante de afiliacion. Los requisitos '
  'dependen del servicio. Informacion administrativa ilustrativa de demo.'
from public.sources s where s.checksum = 'syn_sal_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Orientacion de Navegacion (demostración)',
  'Secretaria de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/navegacion', 'v2026.1', 'active', 'syn_sal_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Limite del Servicio: Solo Navegacion Administrativa (demo)',
  'Contenido de demostración. Este servicio orienta unicamente sobre ubicacion, '
  'servicios, requisitos y horarios. No emite diagnosticos, recetas, dosis ni '
  'interpreta sintomas. Ante una urgencia se indica acudir a la unidad o al 911.'
from public.sources s where s.checksum = 'syn_sal_003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Afiliacion y Vigencia de Derechohabiencia (demostración)',
  'Secretaria de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/afiliacion', 'v2026.1', 'active', 'syn_sal_004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Como Verificar tu Afiliacion (demo)',
  'Contenido de demostración. La afiliacion se verifica en la ventanilla de la '
  'unidad o en el portal de demo con la clave correspondiente. Sirve para conocer '
  'la unidad asignada. Tramite administrativo ilustrativo de demostracion.'
from public.sources s where s.checksum = 'syn_sal_004'
on conflict (source_id, title) do nothing;

-- Fuente VENCIDA: directorio 2024 (caso de vigencia)
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'salud', 'Directorio de Unidades 2024 (vencido, demostración)',
  'Secretaria de Salud (demostración)',
  'https://demo.gobierno-demo.mx/salud/directorio-2024', 'v2024.1', 'expired',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'syn_sal_005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Unidades 2024 (vencido, demo)',
  'Contenido de demostración VENCIDO. Directorio del ejercicio 2024 conservado '
  'como caso negativo de vigencia: menciona unidades por municipio y afiliacion, '
  'pero NO debe aparecer en el retrieval activo. Datos ficticios de demostracion.'
from public.sources s where s.checksum = 'syn_sal_005'
on conflict (source_id, title) do nothing;

-- =============================================================================
-- GANADERIA — 5 fuentes (4 activas + 1 sustituida), 7 documentos
-- =============================================================================

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Expediente e Historial Animal (demostración)',
  'Secretaria de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/expediente', 'v2026.1', 'active', 'syn_gan_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Expediente por Referencia (demo)',
  'Contenido de demostración. El expediente animal se consulta mediante una '
  'referencia opaca (no el arete real). Muestra la ficha y el historial sanitario '
  'del animal autorizado. Datos sinteticos de demostracion, sin trazabilidad real.'
from public.sources s where s.checksum = 'syn_gan_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Historial Sanitario y Vacunas (demo)',
  'Contenido de demostración. El historial reune vacunas aplicadas y eventos '
  'sanitarios del animal. Cada registro incluye tipo, fecha y responsable. '
  'Informacion ilustrativa de demostracion.'
from public.sources s where s.checksum = 'syn_gan_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Registro de Vacunacion (demostración)',
  'Secretaria de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/vacunacion', 'v2026.1', 'active', 'syn_gan_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Como se Registra una Vacuna (demo)',
  'Contenido de demostración. Registrar una vacuna exige nombre, fecha y '
  'confirmacion expresa del productor. La operacion es idempotente: confirmar dos '
  'veces no duplica el registro y devuelve el mismo folio. Flujo de demostracion.'
from public.sources s where s.checksum = 'syn_gan_002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Calendario de Vacunacion Recomendado (demo)',
  'Contenido de demostración. El calendario de demo sugiere aplicaciones '
  'periodicas segun especie y edad. Es una guia administrativa; no sustituye la '
  'indicacion de un medico veterinario. Datos ilustrativos de demostracion.'
from public.sources s where s.checksum = 'syn_gan_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Requisitos de Movilizacion Pecuaria (demostración)',
  'Secretaria de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/movilizacion', 'v2026.1', 'active', 'syn_gan_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Validacion Documental de Movilizacion (demo)',
  'Contenido de demostración. La validacion documental requiere referencia del '
  'animal, destino, historial consultado y alertas consultadas. El resultado es '
  'solo una verificacion documental y NO autoriza por si mismo la movilizacion.'
from public.sources s where s.checksum = 'syn_gan_003'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ganaderia', 'Alertas Sanitarias (demostración)',
  'Secretaria de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/alertas', 'v2026.1', 'active', 'syn_gan_004'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Consulta de Alertas y Zonas de Restriccion (demo)',
  'Contenido de demostración. Las alertas de demo informan zonas con restriccion '
  'temporal de movilizacion por motivos sanitarios. Se consultan antes de validar '
  'una movilizacion. Informacion ficticia de demostracion.'
from public.sources s where s.checksum = 'syn_gan_004'
on conflict (source_id, title) do nothing;

-- Fuente SUSTITUIDA: requisitos de movilizacion 2024 (caso de vigencia)
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)
select t.id, 'ganaderia', 'Requisitos de Movilizacion 2024 (sustituido, demostración)',
  'Secretaria de Agricultura (demostración)',
  'https://demo.gobierno-demo.mx/ganaderia/movilizacion-2024', 'v2024.1', 'superseded',
  '2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z', 'syn_gan_005'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Movilizacion 2024 (sustituido, demo)',
  'Contenido de demostración SUSTITUIDO. Requisitos del ejercicio 2024 '
  'conservados como caso negativo de vigencia: emplean vocabulario casi identico a '
  'los vigentes pero NO deben aparecer en el retrieval activo. Datos de demo.'
from public.sources s where s.checksum = 'syn_gan_005'
on conflict (source_id, title) do nothing;

-- =============================================================================
-- CHUNKS — un chunk por documento, embedding fake determinista.
-- Cubre todos los documentos sembrados arriba (checksums syn_*).
-- =============================================================================

insert into public.chunks (tenant_id, document_id, domain, chunk_index, content, embedding, checksum)
select d.tenant_id, d.id, s.domain, 0, d.content_raw,
  public.fake_embedding(d.content_raw), md5(d.content_raw)
from public.documents d
join public.sources s on s.id = d.source_id
where s.checksum in (
  'syn_veh_001', 'syn_veh_002', 'syn_veh_003', 'syn_veh_004', 'syn_veh_005',
  'syn_emp_001', 'syn_emp_002', 'syn_emp_003', 'syn_emp_004', 'syn_emp_005',
  'syn_rc_001',  'syn_rc_002',  'syn_rc_003',  'syn_rc_004',  'syn_rc_005',
  'syn_sal_001', 'syn_sal_002', 'syn_sal_003', 'syn_sal_004', 'syn_sal_005',
  'syn_gan_001', 'syn_gan_002', 'syn_gan_003', 'syn_gan_004', 'syn_gan_005'
)
and d.content_raw is not null
on conflict (document_id, chunk_index) do nothing;
