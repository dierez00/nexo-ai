-- =============================================================================
-- SaaS v1.3.0 — Seed RAG: Vehículos, Salud y Apertura de Empresas
-- Fuentes y documentos investigados en fuentes oficiales de Durango (2026-07).
-- Contenido real, no inventado: cada fuente cita su source_url. Donde la cifra
-- exacta no estaba disponible en una página .gob.mx (p.ej. costo de licencia
-- de funcionamiento) se redacta "conforme a la Ley de Ingresos vigente" en vez
-- de inventar un número, siguiendo la exclusión de
-- domains/ayuntamiento_empresas/README.md ("no inventar permisos, dependencias
-- ni costos").
-- =============================================================================

-- -----------------------------------------------------------------------------
-- VEHÍCULOS — 2 documentos nuevos sobre la fuente ya sembrada (hash_vehiculos_001)
-- -----------------------------------------------------------------------------

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costo y Descuento de Renovación 2026',
  'El costo de renovación de licencia de conducir vigente es de $985.40 MXN '
  'para automovilista y $657.00 MXN para motociclista, con vigencia de 3 años. '
  'Durante enero de 2026 el Gobierno del Estado de Durango ofreció un descuento '
  'del 50% en la renovación. Los costos se actualizan anualmente en la Ley de '
  'Ingresos del Estado.'
from public.sources s where s.checksum = 'hash_vehiculos_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Ubicación y Horario de Trámite',
  'El trámite de licencia de conducir se realiza en el Departamento de '
  'Recaudación de Rentas, Av. 20 de Noviembre #306, Col. Centro, C.P. 34000, '
  'Durango, Dgo. Horario de atención: 08:00 a 16:00 horas. Teléfono: '
  '618-137-5560. Tiempo estimado de trámite: 20 a 30 minutos, según afluencia.'
from public.sources s where s.checksum = 'hash_vehiculos_001'
on conflict (source_id, title) do nothing;

-- Fuente nueva: Licencia por Primera Vez
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Licencia de Conducir por Primera Vez (Servicio Particular)',
  'Secretaría de Finanzas y de Administración del Estado de Durango',
  'https://www.durango.gob.mx/tramites-y-servicios/fiscalia_del_estado/secretaria_de_finanzas__y_de_administracion/licencia_de_conducir_automovilista_autocamioneta_y_motociclista_servicio_particular_por_primera_vez',
  'v2026.1', 'active', 'hash_vehiculos_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos y Costo — Licencia por Primera Vez',
  'Para tramitar la licencia de conducir por primera vez (servicio particular) '
  'se requiere: solicitud debidamente requisitada (original y 2 copias), '
  'comprobante de domicilio no mayor a 4 meses (original y 1 copia), '
  'identificación oficial vigente (original y 2 copias), acta de nacimiento '
  'certificada que acredite mayoría de edad, y saber leer y escribir. Costo: '
  '$985.00 MXN automovilista, $657.00 MXN motociclista. Vigencia: 3 años. '
  'Trámite en Calle 5 de Febrero #218, Durango, horario 08:00-15:00.'
from public.sources s where s.checksum = 'hash_vehiculos_002'
on conflict (source_id, title) do nothing;

-- Fuente nueva: Refrendo Vehicular 2026
insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'vehiculos', 'Refrendo Vehicular 2026 — Ley de Ingresos del Estado',
  'Congreso del Estado de Durango',
  'https://congresodurango.gob.mx/Archivos/LXX/LEYES-INGRESOS/2026/DURANGO%202026.pdf',
  'v2026.1', 'active', 'hash_vehiculos_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Costo de Refrendo Vehicular 2026',
  'El refrendo vehicular (control vehicular anual) para 2026 tiene un costo '
  'aproximado de $2,430.00 MXN para automóviles, con descuentos por pronto '
  'pago: 15% en enero, 10% en febrero y 5% en marzo (vigencia del descuento '
  'hasta el 31 de marzo de 2026). Desde 2010 el Estado de Durango subsidia al '
  '100% el pago de tenencia vehicular, por lo que los propietarios solo cubren '
  'el refrendo para mantener vigente su tarjeta de circulación.'
from public.sources s where s.checksum = 'hash_vehiculos_003'
on conflict (source_id, title) do nothing;

-- -----------------------------------------------------------------------------
-- SALUD — 3 fuentes nuevas, 5 documentos
-- -----------------------------------------------------------------------------

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'Coordinación de Salud Mental',
  'Secretaría de Salud del Estado de Durango',
  'https://www.durango.gob.mx/tramites-y-servicios/secretarias/secretaria_de_salud_del_estado_de_durango/salud_mental',
  'v2026.1', 'active', 'hash_salud_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Atención Prioritaria en Salud Mental',
  'La Secretaría de Salud del Estado de Durango prioriza la atención a '
  'personas con trastornos de salud mental y en riesgo de vida. El servicio es '
  'gratuito (aplican restricciones). Ubicación: Cuauhtémoc 225 Norte, Zona '
  'Centro, C.P. 34000, Durango. Horario: 08:00 a 14:30 horas. Área '
  'responsable: Coordinación de Atención Hospitalaria.'
from public.sources s where s.checksum = 'hash_salud_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos de Acceso — Salud Mental',
  'Casos no urgentes: se requiere referencia del médico de primer contacto o '
  'del hospital, tras valoración en el centro de salud correspondiente. Casos '
  'de urgencia: admisión directa sin trámite previo. Documentación: constancia '
  'de no afiliación a IMSS/ISSSTE, identificación oficial (adultos) o acta de '
  'nacimiento con identificación del tutor (menores). Resolución: inmediata en '
  'casos de urgencia.'
from public.sources s where s.checksum = 'hash_salud_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'ISMED — Línea Amarilla',
  'Instituto de Salud Mental del Estado de Durango / Secretaría de Seguridad Pública',
  'https://ismed.durango.gob.mx/',
  'v2026.1', 'active', 'hash_salud_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Línea de Crisis "Línea Amarilla" 24/7',
  'La "Línea Amarilla" es un servicio de acompañamiento psicológico y atención '
  'en crisis disponible las 24 horas, los 365 días del año, operado en '
  'coordinación con la Secretaría de Seguridad Pública de Durango dentro de la '
  'campaña "Una Llamada a la Vida". Acceso inmediato marcando al 911. Brinda '
  'acompañamiento gratuito a personas en situación de ansiedad o riesgo '
  'emocional a través de personal capacitado en intervención en crisis.'
from public.sources s where s.checksum = 'hash_salud_002'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Directorio de Emergencia — ISMED',
  'Números de referencia del Instituto de Salud Mental del Estado de Durango: '
  'Emergencias generales 911, Cruz Roja (618) 496-41-79, Protección Civil '
  '(618) 137-96-27, Bomberos (618) 137-84-63, Seguridad Pública (618) 137-40-00.'
from public.sources s where s.checksum = 'hash_salud_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'salud', 'DIF Estatal — Centro de Psicoterapia',
  'Sistema Estatal para el Desarrollo Integral de la Familia (DIF Durango)',
  'https://www.durango.gob.mx/tramites-y-servicios/secretarias/sistema_estatal_para_el_desarrollo_integral_de_la_familia/atencion_psicologica_individual_de_pareja_familiar_y_grupal',
  'v2026.1', 'active', 'hash_salud_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Atención Psicológica Individual, de Pareja, Familiar y Grupal',
  'El Centro de Psicoterapia del DIF Estatal Durango ofrece atención '
  'psicológica individual, de pareja, familiar y grupal, así como '
  'valoraciones psicológicas y acompañamiento en audiencias para niñas, niños '
  'y adolescentes. Está dirigido en especial a grupos vulnerables que no '
  'pueden costear atención particular. Ubicación: Blvd. José María Patoni, '
  'Manzana 105, Predio Rústico La Tinaja y Los Lugos, C.P. 34217, Durango, '
  'Dgo. Solicitud: acudir directamente a las instalaciones o solicitar '
  'información telefónica; también puede solicitarlo una autoridad '
  'jurisdiccional.'
from public.sources s where s.checksum = 'hash_salud_003'
on conflict (source_id, title) do nothing;

-- -----------------------------------------------------------------------------
-- APERTURA DE EMPRESAS (ayuntamiento_empresas) — 3 fuentes nuevas, 4 documentos
-- -----------------------------------------------------------------------------

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Requisitos para Licencia de Funcionamiento',
  'Municipio de Durango — Departamento de Control de Contribuyentes',
  'https://transparencia.municipiodurango.gob.mx/articulo65/XXI/anual/2020/requisitos_para_licencia_de_funcionamiento.pdf',
  'v2020.1', 'active', 'hash_empresas_001'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Requisitos Documentales',
  'Para solicitar la licencia de funcionamiento en el Municipio de Durango se '
  'requiere: nombre completo o razón social del solicitante, denominación del '
  'establecimiento, giro del establecimiento (p.ej. salones para eventos, '
  'hoteles, moteles, spas, entre otros), domicilio para notificaciones dentro '
  'del municipio, dictamen de uso de suelo expedido por la Dirección '
  'Municipal de Desarrollo Urbano, y copia de la Licencia de Funcionamiento o '
  'Constancia de Inscripción Municipal al Padrón de Empresas vigente (en su '
  'caso).'
from public.sources s where s.checksum = 'hash_empresas_001'
on conflict (source_id, title) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Plazos de Resolución por Nivel de Riesgo',
  'El Municipio de Durango resuelve la apertura de empresas de bajo riesgo en '
  'un máximo de 2 días hábiles; giros de mediano riesgo en un máximo de 10 '
  'días hábiles; y licencias de funcionamiento con regulación especial en 20 '
  'días hábiles. El costo se determina conforme a la Ley de Ingresos vigente '
  'del Municipio de Durango. Trámite en el Departamento de Control de '
  'Contribuyentes, Unidad Administrativa Municipal "Gral. Guadalupe '
  'Victoria", Blvd. Luis Donaldo Colosio #200, Fracc. San Ignacio, Durango.'
from public.sources s where s.checksum = 'hash_empresas_001'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'Dictamen de Uso de Suelo',
  'Dirección Municipal de Desarrollo Urbano, Municipio de Durango',
  'https://desarrollourbano.municipiodurango.gob.mx/?page_id=139',
  'v2026.1', 'active', 'hash_empresas_002'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Plazo y Requisito Previo de Uso de Suelo',
  'El dictamen de uso de suelo, requisito previo indispensable para la '
  'licencia de funcionamiento, se resuelve en un plazo máximo de 24 horas '
  'para giros de bajo riesgo y de 5 días hábiles para giros de mediano riesgo '
  'y regulación especial. Todo predio no urbanizado, dentro o fuera de la '
  'mancha urbana, debe tramitar uso de suelo antes de solicitar cualquier '
  'licencia de construcción o funcionamiento.'
from public.sources s where s.checksum = 'hash_empresas_002'
on conflict (source_id, title) do nothing;

insert into public.sources (tenant_id, domain, name, publisher, source_url, version, status, checksum)
select t.id, 'ayuntamiento_empresas', 'SDARE — Sistema de Apertura Rápida de Empresas',
  'Municipio de Durango',
  'https://intram.municipiodurango.gob.mx/wp-content/uploads/2025/08/MANUAL-OPERATIVO-DEL-SDARE.pdf',
  'v2025.1', 'active', 'hash_empresas_003'
from public.tenants t where t.slug = 'gobierno-demo'
on conflict (tenant_id, checksum) do nothing;

insert into public.documents (tenant_id, source_id, title, content_raw)
select s.tenant_id, s.id, 'Qué es el SDARE',
  'El Sistema de Apertura Rápida de Empresas (SDARE) del Municipio de Durango '
  'simplifica y moderniza los trámites municipales para el inicio de '
  'operaciones de negocios de bajo riesgo. El proceso se realiza en el mismo '
  'lugar, en dos visitas del solicitante, en un plazo máximo de 2 a 3 días '
  'hábiles. El municipio se encuentra digitalizando el sistema para permitir '
  'el registro de negocios desde dispositivos móviles.'
from public.sources s where s.checksum = 'hash_empresas_003'
on conflict (source_id, title) do nothing;

-- -----------------------------------------------------------------------------
-- CHUNKS — un chunk por documento, con embedding fake determinista
-- Cubre tanto el documento ya existente de vehículos (hash_vehiculos_001) como
-- todos los documentos nuevos sembrados arriba.
-- -----------------------------------------------------------------------------

insert into public.chunks (tenant_id, document_id, domain, chunk_index, content, embedding, checksum)
select d.tenant_id, d.id, s.domain, 0, d.content_raw,
  public.fake_embedding(d.content_raw), md5(d.content_raw)
from public.documents d
join public.sources s on s.id = d.source_id
where s.checksum in (
  'hash_vehiculos_001', 'hash_vehiculos_002', 'hash_vehiculos_003',
  'hash_salud_001', 'hash_salud_002', 'hash_salud_003',
  'hash_empresas_001', 'hash_empresas_002', 'hash_empresas_003'
)
and d.content_raw is not null
on conflict (document_id, chunk_index) do nothing;
