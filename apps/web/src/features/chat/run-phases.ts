import type { RunEvent } from "@/lib/api/client";

/**
 * Traducción de la traza técnica a las fases que una persona reconoce.
 *
 * El stream trae medio centenar de eventos por run —cada nodo del grafo, cada
 * invocación de modelo, cada checkpoint— y casi ninguno significa nada para
 * quien hace un trámite. Mostrarlos crudos convierte la espera en ruido: el
 * nombre del evento no dice si el sistema está leyendo normativa o esperando una
 * decisión suya.
 *
 * El contrato de eventos es el frozen `contracts/events/run_event.v1.json`; aquí
 * solo se agrupa. Un tipo que no esté mapeado no inventa una fase: se ignora,
 * porque una fase de más es peor que una de menos.
 */
export type PhaseId =
  | "analizando"
  | "consultando_fuentes"
  | "consultando_datos"
  | "esperando_confirmacion"
  | "ejecutando"
  | "completado"
  | "interrumpido";

export type PhaseState = "pendiente" | "en_curso" | "completado" | "fallido";

export type Phase = {
  id: PhaseId;
  label: string;
  detail: string;
  state: PhaseState;
};

const PHASE_ORDER: PhaseId[] = [
  "analizando",
  "consultando_fuentes",
  "consultando_datos",
  "esperando_confirmacion",
  "ejecutando",
  "completado",
  "interrumpido",
];

const PHASE_LABEL: Record<PhaseId, string> = {
  analizando: "Analizando tu solicitud",
  consultando_fuentes: "Consultando fuentes oficiales",
  consultando_datos: "Consultando tus datos",
  esperando_confirmacion: "Esperando tu confirmación",
  ejecutando: "Ejecutando el trámite",
  completado: "Trámite resuelto",
  interrumpido: "No pudimos completar el trámite",
};

/** Qué fase abre cada tipo de evento. Lo no listado no abre ninguna. */
const PHASE_BY_EVENT: Record<string, PhaseId> = {
  "run.queued": "analizando",
  "run.started": "analizando",
  "run.planning": "analizando",
  "classification.started": "analizando",
  "classification.completed": "analizando",
  "plan.created": "analizando",
  "plan.updated": "analizando",
  "rag.started": "consultando_fuentes",
  "rag.completed": "consultando_fuentes",
  "rag.filtered": "consultando_fuentes",
  "tool.requested": "consultando_datos",
  "tool.started": "consultando_datos",
  "tool.completed": "consultando_datos",
  "tool.replayed": "consultando_datos",
  "run.waiting_confirmation": "esperando_confirmacion",
  "tool.authorized": "ejecutando",
  "run.resumed": "ejecutando",
  "run.completed": "completado",
  "run.partial": "completado",
};

/** Eventos que marcan la fase como fallida. */
const FAILURE_EVENTS = new Set([
  "run.failed",
  "run.cancelled",
  "classification.failed",
  "rag.failed",
  "tool.failed",
  "tool.denied",
  "agent.failed",
]);

/**
 * Fallos que se pueden atribuir al paso donde ocurrieron.
 *
 * Los que no están aquí abren la fase terminal `interrumpido` en vez de marcar
 * como fallida la última fase alcanzada: un `run.failed` tras recuperar
 * normativa correctamente no significa que la búsqueda de normativa fallara, y
 * decir lo contrario manda a depurar al sitio equivocado.
 */
const FAILURE_PHASE: Record<string, PhaseId> = {
  "classification.failed": "analizando",
  "rag.failed": "consultando_fuentes",
  "tool.failed": "consultando_datos",
  "tool.denied": "consultando_datos",
};

function numberFrom(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringFrom(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

/**
 * Detalle legible de una fase, tomado del payload del evento.
 *
 * El stream SSE entrega la proyección pública ya en `data` (el servidor la
 * renombra al emitir y elimina `public_data`), mientras que el endpoint de
 * replay devuelve el evento canónico con ambos campos. Se leen los dos para que
 * la línea de tiempo diga lo mismo tanto si llegó en vivo como si se reconstruyó
 * tras recargar la página.
 */
function payloadOf(event: RunEvent): Record<string, unknown> {
  const canonical = (event.public_data ?? {}) as Record<string, unknown>;
  if (Object.keys(canonical).length > 0) return canonical;
  return (event.data ?? {}) as Record<string, unknown>;
}

function detailFor(phase: PhaseId, event: RunEvent, previous: string): string {
  const payload = payloadOf(event);

  if (event.type === "classification.completed") {
    const domain = stringFrom(payload.domain);
    return domain ? `Identificamos un trámite de ${domain.replaceAll("_", " ")}.` : previous;
  }
  if (event.type === "rag.completed") {
    const results = numberFrom(payload.results);
    if (results === null) return previous;
    return results > 0
      ? `${results} ${results === 1 ? "fragmento" : "fragmentos"} de normativa vigente.`
      : "No encontramos normativa vigente para esta consulta.";
  }
  if (event.type === "tool.completed" || event.type === "tool.requested") {
    const tool = stringFrom(payload.tool);
    return tool ? `Consulta a ${tool.replaceAll(".", " · ")}.` : previous;
  }
  if (event.type === "run.waiting_confirmation") {
    const tool = stringFrom(payload.tool);
    return tool
      ? "Revisa los datos y autoriza para continuar."
      : previous || "Revisa los datos y autoriza para continuar.";
  }
  if (event.error?.message) return event.error.message;

  return previous;
}

const DEFAULT_DETAIL: Record<PhaseId, string> = {
  analizando: "Leyendo tu mensaje e identificando el trámite.",
  consultando_fuentes: "Buscando en la normativa publicada.",
  consultando_datos: "Consultando los sistemas de la dependencia.",
  esperando_confirmacion: "Revisa los datos y autoriza para continuar.",
  ejecutando: "Registrando el trámite.",
  completado: "Listo.",
  interrumpido: "La ejecución se detuvo antes de terminar.",
};

/**
 * Reduce la traza a las fases alcanzadas, en orden y sin repetir.
 *
 * `runFinished` cierra la última fase abierta: mientras el run vive, la fase más
 * avanzada se muestra en curso.
 */
export function phasesFromEvents(events: RunEvent[], runFinished = false): Phase[] {
  const reached = new Map<PhaseId, Phase>();

  for (const event of events) {
    const failed = FAILURE_EVENTS.has(event.type) || event.status === "failed";
    const phaseId = failed
      ? (FAILURE_PHASE[event.type] ?? "interrumpido")
      : PHASE_BY_EVENT[event.type];
    if (!phaseId) continue;

    const existing = reached.get(phaseId);
    reached.set(phaseId, {
      id: phaseId,
      label: PHASE_LABEL[phaseId],
      detail: detailFor(phaseId, event, existing?.detail ?? DEFAULT_DETAIL[phaseId]),
      state: failed ? "fallido" : "en_curso",
    });
  }

  const ordered = PHASE_ORDER.filter((id) => reached.has(id)).map(
    (id) => reached.get(id) as Phase,
  );

  return ordered.map((phase, index) => {
    if (phase.state === "fallido") return phase;
    const isLast = index === ordered.length - 1;
    const closed = !isLast || runFinished || phase.id === "completado";
    return { ...phase, state: closed ? "completado" : "en_curso" };
  });
}
