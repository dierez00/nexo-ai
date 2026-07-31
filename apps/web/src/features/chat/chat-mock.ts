export type ChatStateId =
  | "bienvenida"
  | "vacio"
  | "cargando"
  | "error"
  | "sin-resultados"
  | "respuesta"
  | "requisitos"
  | "agendar"
  | "cita-confirmada"
  | "tramite-completado"
  | "seguimiento"
  | "surface-a2ui";

export const estadosChat: { id: ChatStateId; label: string }[] = [
  { id: "bienvenida", label: "Bienvenida" },
  { id: "vacio", label: "Chat vacío" },
  { id: "cargando", label: "Cargando respuesta" },
  { id: "error", label: "Error de conexión" },
  { id: "sin-resultados", label: "Sin resultados" },
  { id: "respuesta", label: "Respuesta exitosa" },
  { id: "requisitos", label: "Requisitos y documentos" },
  { id: "agendar", label: "Agendar cita" },
  { id: "cita-confirmada", label: "Cita agendada" },
  { id: "tramite-completado", label: "Trámite completado" },
  { id: "seguimiento", label: "Seguimiento en progreso" },
  { id: "surface-a2ui", label: "Superficie A2UI (real)" },
];

export const sugerenciasIniciales = [
  "Quiero renovar mi licencia de conducir",
  "¿Cuánto cuesta abrir una empresa unipersonal?",
  "Quiero una copia de mi certificado de nacimiento",
  "¿Dónde registro el hato ganadero?",
];

export const requisitosLicencia = [
  { texto: "Cédula de identidad vigente", ok: true },
  { texto: "Certificado médico de aptitud", ok: true },
  { texto: "Licencia anterior o denuncia de pérdida", ok: false },
  { texto: "Comprobante de pago del arancel", ok: false },
];

export const documentosSubidos = [
  { nombre: "cedula_andrea.pdf", peso: "480 KB", estado: "Validado", tone: "success" as const },
  {
    nombre: "certificado_medico.pdf",
    peso: "620 KB",
    estado: "Validado",
    tone: "success" as const,
  },
  { nombre: "licencia_anterior.pdf", peso: "—", estado: "Falta subir", tone: "warning" as const },
];

export const costosLicencia = [
  { concepto: "Arancel de renovación", monto: "180,00 Bs" },
  { concepto: "Examen médico", monto: "70,00 Bs" },
];

export const eventosSeguimiento = [
  {
    estado: "Solicitud recibida",
    detalle: "Abriste el trámite en el chat y verificamos tu identidad.",
    tone: "success" as const,
    done: true,
  },
  {
    estado: "Documentos recibidos",
    detalle: "Cédula y certificado médico validados automáticamente.",
    tone: "success" as const,
    done: true,
  },
  {
    estado: "En revisión documental",
    detalle: "Falta la licencia anterior o la denuncia de pérdida.",
    tone: "warning" as const,
    active: true,
  },
  {
    estado: "Cita presencial",
    detalle: "Se habilita cuando se completen los requisitos.",
    tone: "neutral" as const,
  },
  {
    estado: "Entrega de la nueva licencia",
    detalle: "Retiro en ventanilla o envío a domicilio.",
    tone: "neutral" as const,
  },
];

export const folioTramite = "NX-2026-005104";
export const placaOTramite = "Renovación de licencia · Andrea Peñaranda";
export const traceIdError = "trc_71fe20aa03";
