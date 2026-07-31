"""Las tools mock del MVP y Core (F1.9 y F2).

Cada tool declara **cuatro cosas juntas**: su metadata versionada, el contrato de
entrada, el contrato de salida y su adapter mock. Están en el mismo sitio a
propósito: separar el schema del adapter es cómo se acaba con un mock que
devuelve algo que su propio contrato rechaza.

Los adapters mock conservan **el wire shape del adapter real futuro**
(`DIE-F1-072`): reciben el input validado y devuelven datos que cumplen el output
schema. Sustituir el mock por una llamada HTTP real no cambia ni el contrato ni
una sola prueba.

**Los nombres de los parámetros son referencias opacas, no datos personales.**
No es una elección estilística: `SafePayload` rechaza claves como `placa`,
`telefono` o `domicilio`, así que una tool que pidiera una placa sería
literalmente inconstruible. Lo que viaja es `vehiculo_ref`, `predio_ref`, y la
resolución a datos reales ocurre en el adapter institucional, fuera de aquí.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Annotated, Any

from pydantic import Field, JsonValue

from nexo_contracts import (
    Domain,
    Money,
    NexoModel,
    RiskLevel,
    ToolMetadata,
    ToolMode,
)

# Reloj fijo de los mocks: los folios y los slots deben ser reproducibles entre
# corridas, o ningún golden test lo sería.
MOCK_NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)
MOCK_TODAY = date(2026, 7, 30)


# ---------------------------------------------------------------------------
# Contratos de entrada y salida
# ---------------------------------------------------------------------------


class ConsultarAdeudoInput(NexoModel):
    vehiculo_ref: str = Field(
        max_length=64,
        description="Referencia opaca del vehículo. Nunca una placa (política de PII).",
    )


class AdeudoConcepto(NexoModel):
    concepto: str = Field(max_length=120)
    monto: Money


class ConsultarAdeudoOutput(NexoModel):
    tiene_adeudo: bool
    total: Money
    conceptos: Annotated[list[AdeudoConcepto], Field(max_length=20)] = Field(default_factory=list)
    bloquea_renovacion: bool = Field(
        description="Si el adeudo impide renovar. Lo decide la dependencia, no el agente."
    )


class LocalizarModuloInput(NexoModel):
    tramite: str = Field(max_length=64)
    zona: str | None = Field(default=None, max_length=64)


class Modulo(NexoModel):
    modulo_id: str = Field(max_length=64)
    nombre: str = Field(max_length=120)
    horario: str = Field(max_length=120)
    tramites: Annotated[list[str], Field(max_length=10)]


class LocalizarModuloOutput(NexoModel):
    modulos: Annotated[list[Modulo], Field(max_length=20)]


class BuscarCitasInput(NexoModel):
    modulo_id: str = Field(max_length=64)
    desde: date
    hasta: date


class Slot(NexoModel):
    slot_id: str = Field(max_length=64)
    inicio: datetime
    disponible: bool = True


class BuscarCitasOutput(NexoModel):
    slots: Annotated[list[Slot], Field(max_length=50)]
    version_catalogo: str = Field(max_length=40)


class ReservarCitaInput(NexoModel):
    slot_id: str = Field(max_length=64)
    vehiculo_ref: str = Field(max_length=64)


class ReservarCitaOutput(NexoModel):
    cita_id: str = Field(max_length=64)
    slot_id: str = Field(max_length=64)
    inicio: datetime


class ConsultarUsoSueloInput(NexoModel):
    giro: str = Field(max_length=80)
    predio_ref: str = Field(max_length=64, description="Referencia opaca del predio.")
    superficie_m2: int = Field(ge=1, le=100_000)


class ConsultarUsoSueloOutput(NexoModel):
    permitido: bool
    zona: str = Field(max_length=16)
    requiere_estacionamiento: bool
    observaciones: Annotated[list[str], Field(max_length=10)] = Field(default_factory=list)


class CalcularCostosInput(NexoModel):
    giro: str = Field(max_length=80)
    tramites: Annotated[list[str], Field(min_length=1, max_length=20)]


class CostoLinea(NexoModel):
    tramite: str = Field(max_length=80)
    monto: Money


class CalcularCostosOutput(NexoModel):
    lineas: Annotated[list[CostoLinea], Field(max_length=20)]
    total: Money


class ConsultarRequisitosInput(NexoModel):
    giro: str = Field(max_length=80)


class ConsultarRequisitosOutput(NexoModel):
    requisitos: Annotated[list[str], Field(max_length=30)]
    tramites_previos: Annotated[list[str], Field(max_length=10)] = Field(default_factory=list)


class ConsultarCitasInput(NexoModel):
    dependencia: str = Field(max_length=80)
    desde: date


class ConsultarCitasOutput(NexoModel):
    slots: Annotated[list[Slot], Field(max_length=50)]


class RegistrarSolicitudInput(NexoModel):
    giro: str = Field(max_length=80)
    predio_ref: str = Field(max_length=64)
    tramite: str = Field(max_length=80)


class RegistrarSolicitudOutput(NexoModel):
    solicitud_id: str = Field(max_length=64)
    tramite: str = Field(max_length=80)
    estado: str = Field(max_length=40)


class ClasificarCorreccionInput(NexoModel):
    descripcion: str = Field(max_length=500)


class ClasificarCorreccionOutput(NexoModel):
    tipo: str = Field(pattern=r"^(copia|aclaracion|correccion)$")
    requiere_pregunta: bool = False
    pregunta: str | None = Field(default=None, max_length=300)


class LocalizarOficialiaInput(NexoModel):
    municipio: str = Field(max_length=100)


class Oficialia(NexoModel):
    oficialia_id: str = Field(max_length=64)
    nombre: str = Field(max_length=160)
    horario: str = Field(max_length=160)


class LocalizarOficialiaOutput(NexoModel):
    oficialias: Annotated[list[Oficialia], Field(max_length=20)]


class DisponibilidadCivilInput(NexoModel):
    oficialia_id: str = Field(max_length=64)
    tramite: str = Field(max_length=80)


class DisponibilidadCivilOutput(NexoModel):
    horarios: Annotated[list[str], Field(max_length=20)]


class SolicitudCivilInput(NexoModel):
    acta_ref: str = Field(max_length=64)
    tipo: str = Field(pattern=r"^(aclaracion|correccion)$")


class SolicitudCivilOutput(NexoModel):
    solicitud_id: str = Field(max_length=64)
    estado: str = Field(max_length=40)


class LocalizarUnidadInput(NexoModel):
    municipio: str = Field(max_length=100)
    afiliacion: str = Field(max_length=80)


class UnidadSalud(NexoModel):
    unidad_id: str = Field(max_length=64)
    nombre: str = Field(max_length=160)
    ubicacion_publica: str = Field(max_length=240)


class LocalizarUnidadOutput(NexoModel):
    unidades: Annotated[list[UnidadSalud], Field(max_length=20)]


class ServicioSaludInput(NexoModel):
    unidad_id: str = Field(max_length=64)


class ServicioSaludOutput(NexoModel):
    servicios: Annotated[list[str], Field(max_length=30)]


class RequisitosSaludInput(NexoModel):
    servicio: str = Field(max_length=100)
    afiliacion: str = Field(max_length=80)


class RequisitosSaludOutput(NexoModel):
    requisitos: Annotated[list[str], Field(max_length=30)]


class HorariosSaludInput(NexoModel):
    unidad_id: str = Field(max_length=64)


class HorariosSaludOutput(NexoModel):
    horarios: Annotated[list[str], Field(max_length=20)]


class ConsultarAnimalInput(NexoModel):
    animal_ref: str = Field(max_length=64)


class ConsultarAnimalOutput(NexoModel):
    animal_ref: str = Field(max_length=64)
    especie: str = Field(max_length=80)
    estado_registro: str = Field(max_length=80)


class HistorialAnimalInput(NexoModel):
    animal_ref: str = Field(max_length=64)


class HistorialAnimalOutput(NexoModel):
    eventos: Annotated[list[str], Field(max_length=50)]


class RegistrarVacunaInput(NexoModel):
    animal_ref: str = Field(max_length=64)
    vacuna: str = Field(max_length=120)
    fecha_aplicacion: date
    actor_ref: str = Field(max_length=64)
    regla_id: str = Field(default="sanidad_demo_2026_01", max_length=80)


class RegistrarVacunaOutput(NexoModel):
    registro_id: str = Field(max_length=64)
    animal_ref: str = Field(max_length=64)
    actor_ref: str = Field(max_length=64)
    regla_id: str = Field(max_length=80)


class ValidarMovilizacionInput(NexoModel):
    animal_ref: str = Field(max_length=64)
    destino: str = Field(max_length=120)


class ValidarMovilizacionOutput(NexoModel):
    permitida: bool
    regla_id: str = Field(max_length=80)
    motivos: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)


class AlertasGanaderasInput(NexoModel):
    municipio: str = Field(max_length=100)


class AlertasGanaderasOutput(NexoModel):
    alertas: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Adapters mock
# ---------------------------------------------------------------------------
#
# Datos sintéticos y deterministas. Coinciden deliberadamente con el corpus de
# `data/documents/`: si la tool dijera 900 MXN y el documento 814 MXN, el
# verificador registraría una contradicción legítima, y estaríamos probando un
# corpus incoherente en vez del sistema.


def _consultar_adeudo(payload: ConsultarAdeudoInput) -> ConsultarAdeudoOutput:
    # La referencia que termina en `_sin_adeudo` no debe nada: es el caso feliz
    # del recorrido oficial.
    if payload.vehiculo_ref.endswith("_sin_adeudo"):
        return ConsultarAdeudoOutput(
            tiene_adeudo=False,
            total=Money(amount_minor=0, currency="MXN"),
            bloquea_renovacion=False,
        )
    return ConsultarAdeudoOutput(
        tiene_adeudo=True,
        total=Money(amount_minor=48000, currency="MXN"),
        conceptos=[
            AdeudoConcepto(
                concepto="Infracción por estacionamiento indebido",
                monto=Money(amount_minor=48000, currency="MXN"),
            )
        ],
        bloquea_renovacion=True,
    )


def _localizar_modulo(payload: LocalizarModuloInput) -> LocalizarModuloOutput:
    modulos = [
        Modulo(
            modulo_id="mod_centro",
            nombre="Módulo Centro",
            horario="Lunes a viernes de 08:00 a 15:00",
            tramites=["renovacion", "primera_emision", "adeudo"],
        ),
        Modulo(
            modulo_id="mod_norte",
            nombre="Módulo Norte",
            horario="Lunes a viernes de 09:00 a 17:00, sábados de 09:00 a 13:00",
            tramites=["renovacion", "adeudo"],
        ),
        Modulo(
            modulo_id="mod_poniente",
            nombre="Módulo Poniente",
            horario="Lunes a jueves de 08:00 a 14:00",
            tramites=["renovacion"],
        ),
    ]
    return LocalizarModuloOutput(
        modulos=[m for m in modulos if payload.tramite in m.tramites] or modulos
    )


def _buscar_citas(payload: BuscarCitasInput) -> BuscarCitasOutput:
    return BuscarCitasOutput(
        slots=[
            Slot(
                slot_id=f"slot_{payload.modulo_id}_{index:02d}",
                inicio=datetime(2026, 8, 3 + index, 9 + index, 0, tzinfo=UTC),
                disponible=True,
            )
            for index in range(3)
        ],
        version_catalogo="citas-2026-07-30",
    )


def _reservar_cita(payload: ReservarCitaInput) -> ReservarCitaOutput:
    return ReservarCitaOutput(
        cita_id=f"apt_{payload.slot_id}",
        slot_id=payload.slot_id,
        inicio=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
    )


def _consultar_uso_suelo(payload: ConsultarUsoSueloInput) -> ConsultarUsoSueloOutput:
    permitido = payload.superficie_m2 <= 60 or "h1" not in payload.predio_ref.lower()
    return ConsultarUsoSueloOutput(
        permitido=permitido,
        zona="H3" if permitido else "H1",
        requiere_estacionamiento=payload.superficie_m2 > 80,
        observaciones=(
            []
            if permitido
            else ["La zona H1 es exclusivamente habitacional y no admite giros comerciales."]
        ),
    )


_TARIFAS_MUNICIPALES: dict[str, int] = {
    "uso_de_suelo": 118000,
    "proteccion_civil": 94000,
    "aviso_sanitario": 0,
    "licencia_funcionamiento": 235000,
}


def _calcular_costos(payload: CalcularCostosInput) -> CalcularCostosOutput:
    lineas = [
        CostoLinea(
            tramite=tramite,
            monto=Money(amount_minor=_TARIFAS_MUNICIPALES.get(tramite, 0), currency="MXN"),
        )
        for tramite in payload.tramites
    ]
    # La suma la hace la tool en enteros, igual que la hará el adapter real. El
    # estimador la recalcula por su cuenta: dos cálculos independientes que
    # deben coincidir es más fuerte que uno solo.
    return CalcularCostosOutput(
        lineas=lineas,
        total=Money(amount_minor=sum(linea.monto.amount_minor for linea in lineas), currency="MXN"),
    )


def _consultar_requisitos(payload: ConsultarRequisitosInput) -> ConsultarRequisitosOutput:
    base = [
        "Identificación oficial vigente",
        "Comprobante de domicilio del establecimiento",
        "Croquis de ubicación",
    ]
    alimentos = payload.giro.lower() in {"taqueria", "taquería", "fonda", "restaurante"}
    return ConsultarRequisitosOutput(
        requisitos=base + (["Constancia de manejo higiénico de alimentos"] if alimentos else []),
        tramites_previos=(
            ["uso_de_suelo", "proteccion_civil", "aviso_sanitario"]
            if alimentos
            else ["uso_de_suelo", "proteccion_civil"]
        ),
    )


def _consultar_citas(payload: ConsultarCitasInput) -> ConsultarCitasOutput:
    return ConsultarCitasOutput(
        slots=[
            Slot(
                slot_id=f"slot_ayto_{index:02d}",
                inicio=datetime(2026, 8, 5 + index, 10, 0, tzinfo=UTC),
            )
            for index in range(2)
        ]
    )


def _registrar_solicitud(payload: RegistrarSolicitudInput) -> RegistrarSolicitudOutput:
    return RegistrarSolicitudOutput(
        solicitud_id=f"sol_{payload.tramite}",
        tramite=payload.tramite,
        estado="recibida",
    )


def _clasificar_correccion(payload: ClasificarCorreccionInput) -> ClasificarCorreccionOutput:
    text = payload.descripcion.casefold()
    if "copia" in text or "certificada" in text:
        return ClasificarCorreccionOutput(tipo="copia")
    if "ortograf" in text or "captura" in text:
        return ClasificarCorreccionOutput(tipo="aclaracion")
    if "dato" in text or "fecha" in text or "apellido" in text:
        return ClasificarCorreccionOutput(tipo="correccion")
    return ClasificarCorreccionOutput(
        tipo="correccion",
        requiere_pregunta=True,
        pregunta="¿El acta tiene un error de captura o necesita cambiar un dato de fondo?",
    )


def _localizar_oficialia(payload: LocalizarOficialiaInput) -> LocalizarOficialiaOutput:
    return LocalizarOficialiaOutput(
        oficialias=[
            Oficialia(
                oficialia_id="oficialia_centro",
                nombre=f"Oficialía Centro de {payload.municipio}",
                horario="Lunes a viernes de 08:30 a 15:00",
            )
        ]
    )


def _disponibilidad_civil(payload: DisponibilidadCivilInput) -> DisponibilidadCivilOutput:
    return DisponibilidadCivilOutput(
        horarios=[
            f"2026-08-04T09:00:00Z · {payload.oficialia_id}",
            f"2026-08-05T11:00:00Z · {payload.tramite}",
        ]
    )


def _registrar_solicitud_civil(payload: SolicitudCivilInput) -> SolicitudCivilOutput:
    return SolicitudCivilOutput(
        solicitud_id=f"sol_rc_{payload.tipo}_{payload.acta_ref[-8:]}",
        estado="recibida",
    )


def _localizar_unidad(payload: LocalizarUnidadInput) -> LocalizarUnidadOutput:
    return LocalizarUnidadOutput(
        unidades=[
            UnidadSalud(
                unidad_id="unidad_centro_demo",
                nombre=f"Centro de Salud Urbano de {payload.municipio}",
                ubicacion_publica="Zona Centro, Durango (ubicación de demostración)",
            )
        ]
    )


def _consultar_servicios(payload: ServicioSaludInput) -> ServicioSaludOutput:
    return ServicioSaludOutput(
        servicios=[
            f"Orientación y medicina preventiva en {payload.unidad_id}",
            "Consulta general sujeta a valoración profesional",
        ]
    )


def _consultar_requisitos_salud(payload: RequisitosSaludInput) -> RequisitosSaludOutput:
    return RequisitosSaludOutput(
        requisitos=[
            "Identificación de la persona responsable",
            "CURP o referencia de registro, si está disponible",
            f"Indicar que se solicita {payload.servicio} con afiliación {payload.afiliacion}",
        ]
    )


def _buscar_horarios_salud(payload: HorariosSaludInput) -> HorariosSaludOutput:
    return HorariosSaludOutput(horarios=[f"Lunes a viernes de 08:00 a 14:00 · {payload.unidad_id}"])


def _consultar_animal(payload: ConsultarAnimalInput) -> ConsultarAnimalOutput:
    return ConsultarAnimalOutput(
        animal_ref=payload.animal_ref,
        especie="bovino",
        estado_registro="activo_sintetico",
    )


def _consultar_historial(payload: HistorialAnimalInput) -> HistorialAnimalOutput:
    return HistorialAnimalOutput(
        eventos=[
            f"2026-01-15 · identificación validada · {payload.animal_ref}",
            "2026-04-10 · revisión sanitaria administrativa",
        ]
    )


def _registrar_vacuna(payload: RegistrarVacunaInput) -> RegistrarVacunaOutput:
    return RegistrarVacunaOutput(
        registro_id=f"vac_{payload.animal_ref[-12:]}_{payload.fecha_aplicacion:%Y%m%d}",
        animal_ref=payload.animal_ref,
        actor_ref=payload.actor_ref,
        regla_id=payload.regla_id,
    )


def _validar_movilizacion(payload: ValidarMovilizacionInput) -> ValidarMovilizacionOutput:
    return ValidarMovilizacionOutput(
        permitida=True,
        regla_id="mov_demo_2026_01",
        motivos=[f"Historial vigente para movilización hacia {payload.destino}"],
    )


def _consultar_alertas(payload: AlertasGanaderasInput) -> AlertasGanaderasOutput:
    return AlertasGanaderasOutput(
        alertas=[f"No hay alertas administrativas activas para {payload.municipio}."]
    )


# ---------------------------------------------------------------------------
# Definiciones
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolDefinition:
    """Una tool completa: metadata, contratos y adapter."""

    metadata: ToolMetadata
    input_model: type[NexoModel]
    output_model: type[NexoModel]
    handler: Callable[[Any], NexoModel]

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    def input_schema(self) -> dict[str, JsonValue]:
        """JSON Schema de entrada, el que publica `tools/list` por MCP."""
        return self.input_model.model_json_schema(by_alias=True)

    def output_schema(self) -> dict[str, JsonValue]:
        """JSON Schema de salida, el que valida el executor tras el adapter.

        Se genera en modo validación y no serialización: `NexoModel` define un
        `model_serializer` envolvente, y en modo serialización Pydantic devuelve
        un `$ref` en lugar de un schema de objeto utilizable.
        """
        return self.output_model.model_json_schema(by_alias=True)


def _metadata(
    name: str,
    domain: Domain,
    *,
    mode: ToolMode = ToolMode.READ,
    risk: RiskLevel = RiskLevel.LOW,
    roles: tuple[str, ...] = ("citizen", "operator"),
    description: str,
    timeout_ms: int = 5000,
) -> ToolMetadata:
    is_write = mode is ToolMode.WRITE
    return ToolMetadata(
        name=name,
        version="1.0.0",
        domain=domain,
        mode=mode,
        risk=risk,
        allowed_roles=list(roles),
        # Una tool de escritura no puede registrarse sin estas tres cosas: el
        # contrato lo rechaza, no este código.
        requires_confirmation=is_write,
        requires_idempotency_key=is_write,
        timeout_ms=timeout_ms,
        max_attempts=1 if is_write else 2,
        input_schema_ref=f"contracts://tools/{name}.input.v1",
        output_schema_ref=f"contracts://tools/{name}.output.v1",
        is_mock=True,
        description=description,
    )


TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        metadata=_metadata(
            "vehiculos.consultar_adeudo",
            Domain.VEHICULOS,
            description="Consulta adeudos e infracciones pendientes. Sin costo.",
        ),
        input_model=ConsultarAdeudoInput,
        output_model=ConsultarAdeudoOutput,
        handler=_consultar_adeudo,
    ),
    ToolDefinition(
        metadata=_metadata(
            "vehiculos.localizar_modulo",
            Domain.VEHICULOS,
            description="Módulos de atención que realizan un trámite, con horarios.",
        ),
        input_model=LocalizarModuloInput,
        output_model=LocalizarModuloOutput,
        handler=_localizar_modulo,
    ),
    ToolDefinition(
        metadata=_metadata(
            "vehiculos.buscar_citas",
            Domain.VEHICULOS,
            description="Slots disponibles en un módulo, versionados.",
        ),
        input_model=BuscarCitasInput,
        output_model=BuscarCitasOutput,
        handler=_buscar_citas,
    ),
    ToolDefinition(
        metadata=_metadata(
            "vehiculos.reservar_cita",
            Domain.VEHICULOS,
            mode=ToolMode.WRITE,
            risk=RiskLevel.MEDIUM,
            roles=("citizen",),
            description="Reserva un slot. Exige confirmación explícita e idempotency key.",
        ),
        input_model=ReservarCitaInput,
        output_model=ReservarCitaOutput,
        handler=_reservar_cita,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ayuntamiento.consultar_uso_suelo",
            Domain.AYUNTAMIENTO_EMPRESAS,
            description="Si un giro está permitido en un predio, según zonificación.",
        ),
        input_model=ConsultarUsoSueloInput,
        output_model=ConsultarUsoSueloOutput,
        handler=_consultar_uso_suelo,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ayuntamiento.calcular_costos",
            Domain.AYUNTAMIENTO_EMPRESAS,
            mode=ToolMode.COMPUTE,
            description="Suma determinista de derechos municipales, en unidades menores.",
        ),
        input_model=CalcularCostosInput,
        output_model=CalcularCostosOutput,
        handler=_calcular_costos,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ayuntamiento.consultar_requisitos_negocio",
            Domain.AYUNTAMIENTO_EMPRESAS,
            description="Requisitos y trámites previos de un giro comercial.",
        ),
        input_model=ConsultarRequisitosInput,
        output_model=ConsultarRequisitosOutput,
        handler=_consultar_requisitos,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ayuntamiento.consultar_citas",
            Domain.AYUNTAMIENTO_EMPRESAS,
            description="Disponibilidad de citas en una dependencia municipal.",
        ),
        input_model=ConsultarCitasInput,
        output_model=ConsultarCitasOutput,
        handler=_consultar_citas,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ayuntamiento.registrar_solicitud",
            Domain.AYUNTAMIENTO_EMPRESAS,
            mode=ToolMode.WRITE,
            risk=RiskLevel.MEDIUM,
            roles=("citizen",),
            description="Inicia una solicitud de trámite. Devuelve folio verificable.",
        ),
        input_model=RegistrarSolicitudInput,
        output_model=RegistrarSolicitudOutput,
        handler=_registrar_solicitud,
    ),
    ToolDefinition(
        metadata=_metadata(
            "registro_civil.clasificar_tipo_correccion",
            Domain.REGISTRO_CIVIL,
            mode=ToolMode.COMPUTE,
            description=(
                "Distingue copia, aclaración y corrección sin resolver cuestiones jurídicas."
            ),
        ),
        input_model=ClasificarCorreccionInput,
        output_model=ClasificarCorreccionOutput,
        handler=_clasificar_correccion,
    ),
    ToolDefinition(
        metadata=_metadata(
            "registro_civil.localizar_oficialia",
            Domain.REGISTRO_CIVIL,
            description="Localiza oficialías y horarios públicos.",
        ),
        input_model=LocalizarOficialiaInput,
        output_model=LocalizarOficialiaOutput,
        handler=_localizar_oficialia,
    ),
    ToolDefinition(
        metadata=_metadata(
            "registro_civil.consultar_disponibilidad",
            Domain.REGISTRO_CIVIL,
            description="Consulta horarios disponibles para orientación presencial.",
        ),
        input_model=DisponibilidadCivilInput,
        output_model=DisponibilidadCivilOutput,
        handler=_disponibilidad_civil,
    ),
    ToolDefinition(
        metadata=_metadata(
            "registro_civil.registrar_solicitud",
            Domain.REGISTRO_CIVIL,
            mode=ToolMode.WRITE,
            risk=RiskLevel.MEDIUM,
            roles=("citizen",),
            description="Registra una solicitud mock; nunca modifica un acta.",
        ),
        input_model=SolicitudCivilInput,
        output_model=SolicitudCivilOutput,
        handler=_registrar_solicitud_civil,
    ),
    ToolDefinition(
        metadata=_metadata(
            "salud.localizar_unidad_salud",
            Domain.SALUD,
            description="Localiza unidades para navegación de servicios, sin triage clínico.",
        ),
        input_model=LocalizarUnidadInput,
        output_model=LocalizarUnidadOutput,
        handler=_localizar_unidad,
    ),
    ToolDefinition(
        metadata=_metadata(
            "salud.consultar_servicios",
            Domain.SALUD,
            description="Lista servicios administrativos publicados por una unidad.",
        ),
        input_model=ServicioSaludInput,
        output_model=ServicioSaludOutput,
        handler=_consultar_servicios,
    ),
    ToolDefinition(
        metadata=_metadata(
            "salud.consultar_requisitos",
            Domain.SALUD,
            description="Consulta requisitos administrativos; no interpreta síntomas.",
        ),
        input_model=RequisitosSaludInput,
        output_model=RequisitosSaludOutput,
        handler=_consultar_requisitos_salud,
    ),
    ToolDefinition(
        metadata=_metadata(
            "salud.buscar_horarios",
            Domain.SALUD,
            description="Consulta horarios publicados de una unidad.",
        ),
        input_model=HorariosSaludInput,
        output_model=HorariosSaludOutput,
        handler=_buscar_horarios_salud,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ganaderia.consultar_animal",
            Domain.GANADERIA,
            roles=("producer", "operator"),
            description="Consulta un animal por referencia sintética/autorizada.",
        ),
        input_model=ConsultarAnimalInput,
        output_model=ConsultarAnimalOutput,
        handler=_consultar_animal,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ganaderia.consultar_historial",
            Domain.GANADERIA,
            roles=("producer", "operator"),
            description="Consulta historial sanitario administrativo.",
        ),
        input_model=HistorialAnimalInput,
        output_model=HistorialAnimalOutput,
        handler=_consultar_historial,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ganaderia.registrar_vacuna",
            Domain.GANADERIA,
            mode=ToolMode.WRITE,
            risk=RiskLevel.HIGH,
            roles=("producer", "operator"),
            description="Registra una vacuna mock con confirmación, idempotencia y folio.",
        ),
        input_model=RegistrarVacunaInput,
        output_model=RegistrarVacunaOutput,
        handler=_registrar_vacuna,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ganaderia.validar_movilizacion",
            Domain.GANADERIA,
            mode=ToolMode.COMPUTE,
            roles=("producer", "operator"),
            description="Evalúa movilización contra una regla vigente identificada.",
        ),
        input_model=ValidarMovilizacionInput,
        output_model=ValidarMovilizacionOutput,
        handler=_validar_movilizacion,
    ),
    ToolDefinition(
        metadata=_metadata(
            "ganaderia.consultar_alertas",
            Domain.GANADERIA,
            roles=("producer", "operator"),
            description="Devuelve únicamente alertas administrativas autorizadas.",
        ),
        input_model=AlertasGanaderasInput,
        output_model=AlertasGanaderasOutput,
        handler=_consultar_alertas,
    ),
)

DEFINITIONS_BY_NAME: dict[str, ToolDefinition] = {
    definition.name: definition for definition in TOOL_DEFINITIONS
}
