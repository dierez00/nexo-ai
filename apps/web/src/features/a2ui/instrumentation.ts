/**
 * Instrumentación de la línea de tiempo de una superficie.
 *
 * La pregunta que responde es "¿cuánto tarda una persona en ver componentes?",
 * no "¿cuánto tarda el modelo?". El modelo no genera A2UI: el builder de
 * servidor es determinista y produce la superficie desde plantillas y hechos
 * verificados (ADR 0006). El modelo actúa **antes**, produciendo esos hechos.
 *
 * Por eso hay dos tramos que este archivo no puede medir todavía y se declaran
 * como bloqueados en vez de omitirse: cuando el backend emita la superficie por
 * el SSE del run, la misma tabla se llena sola.
 */

export type SegmentId = "model" | "server" | "transport" | "parse" | "guard" | "render" | "total";

export type Segment = {
  id: SegmentId;
  label: string;
  ms: number | null;
  /** Por qué no hay número todavía. */
  blockedBy?: string;
};

export type Timeline = {
  fixture: string;
  segments: Segment[];
};

/** Percentil por interpolación de índice; con pocas muestras es lo honesto. */
export function percentile(values: number[], q: number): number {
  if (values.length === 0) return 0;
  const ordered = [...values].sort((a, b) => a - b);
  const index = Math.min(Math.floor(q * ordered.length), ordered.length - 1);
  return ordered[index];
}

export function round(value: number, decimals = 3): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

export type Sample = {
  transportMs: number;
  parseMs: number;
  guardMs: number;
  /**
   * Desde que React recibe el estado hasta que el frame se pintó.
   *
   * No usa `<Profiler>` porque React lo desactiva en builds de producción y
   * reportaría 0 ms — un cero que parece una medición y no lo es. Esto mide el
   * commit más el primer frame, y da el mismo número en dev y en producción.
   */
  renderMs: number;
  totalMs: number;
};

export type Aggregate = {
  runs: number;
  transport: { p50: number; p95: number };
  parse: { p50: number; p95: number };
  guard: { p50: number; p95: number };
  render: { p50: number; p95: number };
  total: { p50: number; p95: number };
};

export function aggregate(samples: Sample[]): Aggregate {
  const pick = (key: keyof Sample) => {
    const values = samples.map((sample) => sample[key]);
    return { p50: round(percentile(values, 0.5)), p95: round(percentile(values, 0.95)) };
  };
  return {
    runs: samples.length,
    transport: pick("transportMs"),
    parse: pick("parseMs"),
    guard: pick("guardMs"),
    render: pick("renderMs"),
    total: pick("totalMs"),
  };
}

/**
 * Resuelve justo después de que el navegador pintó el frame.
 *
 * `requestAnimationFrame` corre **antes** de pintar, así que por sí solo no
 * sirve. El truco es encolar un mensaje desde dentro del rAF: los mensajes se
 * entregan después de que el frame se pintó. Dos rAF encadenados también
 * funcionan, pero esperan un frame de más y ese frame se cuela en la medición
 * como si fuera trabajo de la aplicación.
 *
 * Aun así queda un piso: nunca puede salir menos que lo que falte para el
 * siguiente frame (~16 ms a 60 Hz). El tramo que usa esto lo declara.
 */
export function afterPaint(): Promise<number> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      const channel = new MessageChannel();
      channel.port1.onmessage = () => {
        channel.port1.close();
        resolve(performance.now());
      };
      channel.port2.postMessage(undefined);
    });
  });
}
