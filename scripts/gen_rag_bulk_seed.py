"""Generador del seed RAG sintético MASIVO para el runtime.

Emite `supabase/migrations/20260731130000_rag_seed_domain_datasets_bulk.sql`,
que amplía el corpus que consulta el runtime en vivo
(`public.sources/documents/chunks` vía `public.match_chunks`) con DECENAS de
fuentes por dominio (por defecto 40 → ~200 fuentes / ~400 documentos / ~400
chunks para los 5 dominios).

Diseño (idéntico patrón que 20260731120000_rag_seed_domain_datasets_full.sql,
con namespace de checksum PROPIO `bulk_<dom>_NNNN` para no colisionar ni con los
hashes reales `hash_*` ni con los `syn_*`):

  * Contenido 100% SINTÉTICO de demostración, marcado "(demostración)" en cada
    fuente y documento. Sin PII ni credenciales; cifras ilustrativas, no
    oficiales. Salud se limita a NAVEGACIÓN ADMINISTRATIVA (sin diagnóstico,
    receta, dosis ni interpretación de síntomas), conforme a
    domains/salud/safety_policy.yaml.
  * Idempotente por las constraints ya existentes
    (sources_tenant_checksum_key, documents_source_title_key,
    chunks_document_chunk_index_key) usando `on conflict ... do nothing`.
  * Cada dominio incluye ≥2 fuentes vencidas/sustituidas (expired/superseded)
    para ejercitar el filtro de vigencia de match_chunks.
  * Un chunk por documento, embedding determinista `public.fake_embedding`.

Salida DETERMINISTA: dos ejecuciones producen exactamente el mismo .sql.
Uso:  uv run python scripts/gen_rag_bulk_seed.py
Para más volumen: subir SOURCES_PER_DOMAIN y regenerar.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = (
    REPO_ROOT / "supabase" / "migrations"
    / "20260731130000_rag_seed_domain_datasets_bulk.sql"
)

# --- Parámetros de escala (ajustables) -------------------------------------
SOURCES_PER_DOMAIN = 40
# Nº de documentos por fuente en función del índice (ciclo 2,3,1,2,3,1,...).
DOCS_CYCLE = (2, 3, 1)
# Índices (0-based) que se marcan como vencidos/sustituidos por dominio.
SUPERSEDED_INDICES = {8, 24}   # status = 'superseded'
EXPIRED_INDICES = {16, 32}     # status = 'expired'


def esc(text: str) -> str:
    """Escapa comillas simples para un literal SQL."""
    return text.replace("'", "''")


# --- Bancos temáticos por dominio ------------------------------------------
# Cada tema aporta un stub de título y una lista de frases de cuerpo. El
# generador combina tema + ejes de variación para producir texto diverso.

ZONAS = [
    "zona centro", "zona norte", "zona sur", "zona oriente", "zona poniente",
    "corredor industrial", "cabecera municipal", "distrito histórico",
]
DIAS = [
    "de lunes a viernes en horario matutino",
    "de lunes a sábado con horario ampliado",
    "de lunes a viernes en horario corrido",
    "de martes a sábado en horario vespertino",
]
PLAZOS = [
    "en pocos días hábiles", "dentro de la misma semana",
    "en un plazo estimado de 24 a 72 horas", "en el transcurso del mes",
]


DomainSpec = dict


def domain_specs() -> list[DomainSpec]:
    return [
        {
            "domain": "vehiculos",
            "prefix": "veh",
            "publisher": "Instituto de Control Vehicular de Durango (demostración)",
            "url_base": "https://demo.gobierno-demo.mx/vehiculos",
            "themes": [
                ("Requisitos de Renovación de Licencia",
                 "Para renovar la licencia de conducir se presenta identificacion "
                 "oficial vigente, comprobante de domicilio reciente, la licencia "
                 "anterior y el comprobante de pago de derechos."),
                ("Tarifario de Trámites Vehiculares",
                 "Las tarifas ilustrativas cubren renovacion, expedicion por primera "
                 "vez y refrendo anual de control vehicular; los montos son de "
                 "demostracion y no representan tarifas oficiales."),
                ("Consulta de Adeudos y Refrendo",
                 "El adeudo vehicular se consulta con el numero de placa o de serie; "
                 "el sistema muestra refrendos pendientes y multas asociadas."),
                ("Módulos de Atención Vehicular",
                 "Los modulos de atencion operan con distinta cobertura y reciben "
                 "renovaciones, refrendos y reposiciones de tarjeta de circulacion."),
                ("Cita Previa Vehicular",
                 "Se recomienda agendar cita previa para reducir el tiempo de espera; "
                 "la reserva es idempotente y confirmar dos veces no duplica la cita."),
                ("Reposición de Placas y Tarjeta",
                 "La reposicion por robo o extravio requiere denuncia o reporte y el "
                 "comprobante de pago; el tramite es presencial en un modulo."),
                ("Verificación Vehicular Ambiental",
                 "El calendario de verificacion se organiza por terminacion de placa; "
                 "el resultado se registra en el historial del vehiculo."),
                ("Licencias para Motociclista",
                 "La licencia de motociclista contempla vigencias diferenciadas y "
                 "puede requerir evaluacion practica adicional segun el tipo."),
                ("Descuentos por Pronto Pago",
                 "En el ejercicio de demo se aplican descuentos por pronto pago del "
                 "refrendo, decrecientes durante el primer trimestre del anio."),
                ("Trámite de Baja Vehicular",
                 "La baja vehicular exige la documentacion del vehiculo y la "
                 "acreditacion del propietario; libera obligaciones de refrendo."),
            ],
        },
        {
            "domain": "ayuntamiento_empresas",
            "prefix": "emp",
            "publisher": "Dirección de Desarrollo Urbano (demostración)",
            "url_base": "https://demo.gobierno-demo.mx/empresas",
            "themes": [
                ("Dictamen de Uso de Suelo",
                 "El dictamen de uso de suelo es el requisito previo indispensable "
                 "para la licencia de funcionamiento y verifica si el giro esta "
                 "permitido en el domicilio."),
                ("Protección Civil para Negocios",
                 "Los giros de mediano riesgo requieren visto bueno de proteccion "
                 "civil: extintores vigentes, senializacion y salidas de emergencia."),
                ("Aviso de Funcionamiento Sanitario",
                 "Los establecimientos que manejan alimentos presentan aviso de "
                 "funcionamiento sanitario y designan un responsable de higiene."),
                ("Sistema de Apertura Rápida (SDARE)",
                 "El sistema de apertura rapida simplifica los tramites para negocios "
                 "de bajo riesgo, resolviendo la apertura en un mismo punto."),
                ("Costos Municipales de Apertura",
                 "Los costos de la licencia de funcionamiento se determinan conforme "
                 "a la ley de ingresos vigente de demo, segun giro y nivel de riesgo."),
                ("Licencia de Anuncios y Publicidad",
                 "La colocacion de anuncios en fachada requiere licencia especifica "
                 "que evalua dimensiones, seguridad estructural e imagen urbana."),
                ("Giros con Venta de Alcohol",
                 "La venta de bebidas alcoholicas exige anuencia adicional y horarios "
                 "regulados; el giro se clasifica de mayor riesgo administrativo."),
                ("Refrendo Anual de Licencia",
                 "La licencia de funcionamiento se refrenda cada ejercicio "
                 "presentando el pago correspondiente y datos actualizados del giro."),
                ("Inspección y Verificación de Giros",
                 "La verificacion documental confirma que el establecimiento cumple "
                 "las condiciones declaradas; no sustituye una inspeccion fisica."),
                ("Ventanilla Única Empresarial",
                 "La ventanilla unica concentra la orientacion sobre tramites de "
                 "apertura y turna cada requisito a la dependencia competente."),
            ],
        },
        {
            "domain": "registro_civil",
            "prefix": "rc",
            "publisher": "Registro Civil (demostración)",
            "url_base": "https://demo.gobierno-demo.mx/registro-civil",
            "themes": [
                ("Copias Certificadas de Actas",
                 "La copia certificada de un acta se obtiene de forma presencial en "
                 "una oficialia con identificacion oficial y los datos registrales."),
                ("Aclaración de Actas",
                 "Un error de ortografia, captura o transcripcion se resuelve por "
                 "aclaracion administrativa sin modificar el fondo del registro."),
                ("Corrección de Datos de Fondo",
                 "Cambiar un dato de fondo como apellido o fecha se tramita como "
                 "correccion y puede requerir revision de la oficialia."),
                ("Directorio de Oficialías",
                 "El directorio lista oficialias por zona; cada una atiende copias, "
                 "aclaraciones y correcciones dentro de su circunscripcion."),
                ("Disponibilidad de Citas",
                 "La disponibilidad de citas se consulta por oficialia y tipo de "
                 "tramite; el sistema muestra horarios libres y permite reservar."),
                ("Acta de Nacimiento",
                 "El acta de nacimiento se emite con los datos del registro original; "
                 "la copia certificada tiene la misma validez que el asiento."),
                ("Acta de Matrimonio",
                 "La copia certificada del acta de matrimonio requiere los datos de "
                 "la partida y una identificacion de la persona solicitante."),
                ("Acta de Defunción",
                 "La copia certificada del acta de defuncion se solicita con los "
                 "datos registrales; sirve para tramites sucesorios y administrativos."),
                ("Registro Extemporáneo",
                 "El registro extemporaneo aplica cuando el asiento se realiza fuera "
                 "del plazo ordinario y puede requerir documentacion de respaldo."),
                ("Constancias de Inexistencia",
                 "La constancia de inexistencia acredita que no obra un registro "
                 "determinado y se emite tras la busqueda en el archivo."),
            ],
        },
        {
            "domain": "salud",
            "prefix": "sal",
            "publisher": "Secretaría de Salud (demostración)",
            "url_base": "https://demo.gobierno-demo.mx/salud",
            # SOLO navegación administrativa (safety_policy.yaml): sin diagnóstico,
            # receta, dosis ni interpretación de síntomas.
            "themes": [
                ("Directorio de Unidades de Salud",
                 "La unidad aplicable depende del municipio y la afiliacion; el "
                 "directorio orienta a que unidad acudir de forma administrativa."),
                ("Catálogo de Servicios Administrativos",
                 "Se orienta sobre servicios administrativos como agenda de citas y "
                 "ventanilla de afiliacion; no se ofrece diagnostico ni tratamiento."),
                ("Afiliación y Vigencia de Derechohabiencia",
                 "La afiliacion se verifica en la ventanilla de la unidad o en el "
                 "portal de demo y sirve para conocer la unidad asignada."),
                ("Horarios de Atención",
                 "Las unidades atienden en horario matutino y vespertino; la "
                 "informacion es unicamente administrativa y de ubicacion."),
                ("Requisitos Documentales",
                 "Para tramites administrativos suele solicitarse identificacion "
                 "oficial y, en su caso, comprobante de afiliacion."),
                ("Límite del Servicio de Orientación",
                 "Este servicio orienta unicamente sobre ubicacion, servicios, "
                 "requisitos y horarios; ante una urgencia se indica acudir al 911."),
                ("Ventanilla de Citas Administrativas",
                 "La ventanilla gestiona el registro y la reprogramacion de citas de "
                 "primer contacto de manera puramente administrativa."),
                ("Traslado entre Unidades",
                 "El cambio de unidad asignada es un tramite administrativo que "
                 "actualiza el registro de adscripcion de la persona."),
                ("Módulos de Afiliación",
                 "Los modulos de afiliacion reciben altas y actualizaciones de datos "
                 "de derechohabiencia dentro de su cobertura territorial."),
                ("Constancia de Vigencia de Derechos",
                 "La constancia de vigencia acredita administrativamente la "
                 "afiliacion y se descarga o se solicita en ventanilla."),
            ],
        },
        {
            "domain": "ganaderia",
            "prefix": "gan",
            "publisher": "Secretaría de Agricultura (demostración)",
            "url_base": "https://demo.gobierno-demo.mx/ganaderia",
            "themes": [
                ("Expediente e Historial Animal",
                 "El expediente animal se consulta mediante una referencia opaca (no "
                 "el arete real) y muestra la ficha y el historial sanitario."),
                ("Registro de Vacunación",
                 "Registrar una vacuna exige nombre, fecha y confirmacion expresa del "
                 "productor; la operacion es idempotente y devuelve el mismo folio."),
                ("Requisitos de Movilización Pecuaria",
                 "La validacion documental requiere referencia del animal, destino e "
                 "historial; el resultado NO autoriza por si mismo la movilizacion."),
                ("Alertas Sanitarias y Zonas de Restricción",
                 "Las alertas informan zonas con restriccion temporal de movilizacion "
                 "por motivos sanitarios y se consultan antes de validar un traslado."),
                ("Calendario de Vacunación Recomendado",
                 "El calendario sugiere aplicaciones periodicas segun especie y edad; "
                 "es una guia administrativa que no sustituye al medico veterinario."),
                ("Constancia de Hato",
                 "La constancia de hato describe la composicion declarada del predio "
                 "con fines administrativos y de trazabilidad de demostracion."),
                ("Aretado e Identificación",
                 "El aretado asigna una referencia opaca al animal para su "
                 "seguimiento; la referencia no revela datos personales del productor."),
                ("Guía de Tránsito Interno",
                 "La guia de transito interno documenta el desplazamiento entre "
                 "predios de un mismo productor dentro de la misma circunscripcion."),
                ("Registro de Unidades de Producción",
                 "El registro de la unidad de produccion vincula el predio con su "
                 "responsable declarado y habilita otros tramites pecuarios."),
                ("Control de Eventos Sanitarios",
                 "Cada evento sanitario se asienta con tipo, fecha y responsable en el "
                 "historial del animal para su consulta posterior."),
            ],
        },
    ]


def build_content(theme_body: str, i: int, doc_n: int) -> str:
    """Cuerpo sintético variado y compliant, distinto por (fuente, documento)."""
    zona = ZONAS[(i + doc_n) % len(ZONAS)]
    dias = DIAS[(i + doc_n) % len(DIAS)]
    plazo = PLAZOS[(i * 2 + doc_n) % len(PLAZOS)]
    return (
        "Contenido de demostración. "
        f"{theme_body} En el ejercicio de demo la atencion en {zona} opera {dias}, "
        f"y los tramites relacionados se resuelven {plazo}. "
        "Datos ilustrativos de demostracion; no representan un tramite oficial real "
        "ni reproducen documentos institucionales."
    )


def status_for(i: int) -> tuple[str, str | None, str | None]:
    """(status, valid_from, valid_to) — vencidas/sustituidas en índices fijos."""
    if i in SUPERSEDED_INDICES:
        return "superseded", "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"
    if i in EXPIRED_INDICES:
        return "expired", "2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"
    return "active", None, None


def gen_domain_block(spec: DomainSpec) -> list[str]:
    prefix = spec["prefix"]
    domain = spec["domain"]
    publisher = esc(spec["publisher"])
    url_base = spec["url_base"]
    themes = spec["themes"]
    lines: list[str] = []
    lines.append(
        "-- =========================================================================\n"
        f"-- {domain.upper()} — {SOURCES_PER_DOMAIN} fuentes (namespace bulk_{prefix}_*)\n"
        "-- ========================================================================="
    )
    for i in range(SOURCES_PER_DOMAIN):
        checksum = f"bulk_{prefix}_{i + 1:04d}"
        theme_title, theme_body = themes[i % len(themes)]
        # Título de fuente único por variante temática.
        variante = (i // len(themes)) + 1
        source_name = esc(
            f"{theme_title} — variante {variante} (demostración)"
        )
        version = f"v2026.{variante}"
        status, valid_from, valid_to = status_for(i)
        url = f"{url_base}/{prefix}-{i + 1:04d}"

        if valid_from is None:
            lines.append(
                "\ninsert into public.sources "
                "(tenant_id, domain, name, publisher, source_url, version, status, checksum)\n"
                f"select t.id, '{domain}', '{source_name}',\n"
                f"  '{publisher}',\n"
                f"  '{url}', '{version}', '{status}', '{checksum}'\n"
                "from public.tenants t where t.slug = 'gobierno-demo'\n"
                "on conflict (tenant_id, checksum) do nothing;"
            )
        else:
            lines.append(
                "\ninsert into public.sources "
                "(tenant_id, domain, name, publisher, source_url, version, status, valid_from, valid_to, checksum)\n"
                f"select t.id, '{domain}', '{source_name}',\n"
                f"  '{publisher}',\n"
                f"  '{url}', '{version}', '{status}',\n"
                f"  '{valid_from}', '{valid_to}', '{checksum}'\n"
                "from public.tenants t where t.slug = 'gobierno-demo'\n"
                "on conflict (tenant_id, checksum) do nothing;"
            )

        docs_n = DOCS_CYCLE[i % len(DOCS_CYCLE)]
        for d in range(docs_n):
            doc_title = esc(f"{theme_title} — documento {d + 1} (demo, {checksum})")
            content = esc(build_content(theme_body, i, d))
            lines.append(
                "\ninsert into public.documents (tenant_id, source_id, title, content_raw)\n"
                f"select s.tenant_id, s.id, '{doc_title}',\n"
                f"  '{content}'\n"
                f"from public.sources s where s.checksum = '{checksum}'\n"
                "on conflict (source_id, title) do nothing;"
            )
    return lines


def main() -> None:
    parts: list[str] = []
    parts.append(
        "-- =============================================================================\n"
        "-- SaaS v1.3.0 — Seed RAG BULK: corpus sintético masivo por dominio (5 módulos)\n"
        "-- =============================================================================\n"
        "-- GENERADO por scripts/gen_rag_bulk_seed.py (NO editar a mano; regenerar).\n"
        "--\n"
        f"-- Amplía el corpus del runtime con {SOURCES_PER_DOMAIN} fuentes por dominio\n"
        "-- (~200 fuentes / ~400 documentos / ~400 chunks) para los CINCO dominios:\n"
        "-- vehiculos, ayuntamiento_empresas, registro_civil, salud y ganaderia.\n"
        "--\n"
        "-- Contenido 100% SINTÉTICO de demostración (marcado \"(demostración)\"): sin\n"
        "-- PII ni credenciales; cifras ilustrativas, no oficiales. Salud se limita a\n"
        "-- NAVEGACIÓN ADMINISTRATIVA (domains/salud/safety_policy.yaml).\n"
        "--\n"
        "-- Namespace de checksum PROPIO `bulk_<dom>_NNNN` para NO colisionar con los\n"
        "-- hashes reales `hash_*` (20260504190000) ni con `syn_*` (20260731120000).\n"
        "--\n"
        "-- Idempotente por las constraints existentes:\n"
        "--   sources_tenant_checksum_key (tenant_id, checksum)\n"
        "--   documents_source_title_key  (source_id, title)\n"
        "--   chunks_document_chunk_index_key (document_id, chunk_index)\n"
        "-- Cada dominio incluye fuentes vencidas/sustituidas (expired/superseded)\n"
        "-- para ejercitar el filtro de vigencia de public.match_chunks.\n"
        "-- ============================================================================="
    )
    for spec in domain_specs():
        parts.extend(gen_domain_block(spec))

    # Bloque final de chunks: un chunk por documento de todo el namespace bulk_*.
    parts.append(
        "\n-- =============================================================================\n"
        "-- CHUNKS — un chunk por documento, embedding fake determinista.\n"
        "-- Cubre todos los documentos sembrados arriba (checksums bulk_*).\n"
        "-- =============================================================================\n"
        "\ninsert into public.chunks (tenant_id, document_id, domain, chunk_index, content, embedding, checksum)\n"
        "select d.tenant_id, d.id, s.domain, 0, d.content_raw,\n"
        "  public.fake_embedding(d.content_raw), md5(d.content_raw)\n"
        "from public.documents d\n"
        "join public.sources s on s.id = d.source_id\n"
        "where s.checksum like 'bulk\\_%'\n"
        "and d.content_raw is not null\n"
        "on conflict (document_id, chunk_index) do nothing;"
    )

    sql = "\n".join(parts) + "\n"
    OUT_FILE.write_text(sql, encoding="utf-8")
    total_sources = SOURCES_PER_DOMAIN * 5
    print(f"Escrito {OUT_FILE.relative_to(REPO_ROOT)}")
    print(f"Fuentes: {total_sources}  (por dominio: {SOURCES_PER_DOMAIN})")


if __name__ == "__main__":
    main()
