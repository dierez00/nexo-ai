import type { Metadata } from "next";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { Rail, RailItem } from "@/components/nexo/rail";

export const metadata: Metadata = {
  title: "Workflow del agente — Nexo AI",
  description: "Grafo de nodos del flujo del agente y línea de tiempo de eventos.",
  openGraph: {
    title: "Workflow del agente — Nexo AI",
    description: "Cómo fluye una solicitud entre nodos y herramientas.",
  },
};

type Nodo = {
  id: string;
  label: string;
  sub: string;
  x: number;
  y: number;
  tone: Tone;
  estado: string;
};

const nodos: Nodo[] = [
  {
    id: "in",
    label: "Ingreso",
    sub: "WhatsApp · voz · web",
    x: 60,
    y: 40,
    tone: "info",
    estado: "OK",
  },
  {
    id: "cls",
    label: "Clasificador",
    sub: "detecta dominio",
    x: 60,
    y: 150,
    tone: "success",
    estado: "OK",
  },
  {
    id: "req",
    label: "Requisitos",
    sub: "tool: consultar_requisitos",
    x: 300,
    y: 100,
    tone: "success",
    estado: "OK",
  },
  {
    id: "doc",
    label: "Validador docs",
    sub: "tool: validar_documento",
    x: 300,
    y: 210,
    tone: "warning",
    estado: "Lento",
  },
  {
    id: "cit",
    label: "Agenda",
    sub: "tool: reservar_cita",
    x: 540,
    y: 100,
    tone: "success",
    estado: "OK",
  },
  {
    id: "hum",
    label: "Derivación",
    sub: "operador humano",
    x: 540,
    y: 210,
    tone: "neutral",
    estado: "En espera",
  },
];

const aristas: [string, string][] = [
  ["in", "cls"],
  ["cls", "req"],
  ["cls", "doc"],
  ["req", "cit"],
  ["doc", "hum"],
  ["doc", "cit"],
];

const W = 160;
const H = 66;

function centro(n: Nodo) {
  return { x: n.x + W / 2, y: n.y + H / 2 };
}

const eventos = [
  {
    t: "09:41:02",
    titulo: "Mensaje recibido",
    detalle: "Canal WhatsApp · usuario verificado",
    done: true,
  },
  {
    t: "09:41:03",
    titulo: "Dominio clasificado",
    detalle: "Vehículos · confianza 0,96",
    done: true,
  },
  {
    t: "09:41:04",
    titulo: "Herramienta ejecutada",
    detalle: "consultar_requisitos · 320 ms",
    done: true,
  },
  {
    t: "09:41:07",
    titulo: "Documento validado",
    detalle: "titulo_propiedad.pdf · 1,9 s (por encima del umbral)",
    done: true,
  },
  {
    t: "09:41:12",
    titulo: "Confirmación solicitada",
    detalle: "Cita 12/08 10:00 · esperando al ciudadano",
    activo: true,
  },
];

export default function Page() {
  return (
    <AdminShell
      title="Workflow"
      subtitle="Flujo del agente para el dominio Vehículos · versión 4.2"
      actions={<StatusBadge tone="warning">1 nodo degradado</StatusBadge>}
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-border px-5 py-3">
            <h2 className="truncate text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Grafo de nodos
            </h2>
            <StatusBadge tone="accent">Ejecución run_9f2a41</StatusBadge>
          </div>
          <div className="overflow-x-auto p-4">
            <svg viewBox="0 0 760 320" className="h-[320px] w-[720px] min-w-[720px]">
              {aristas.map(([a, b]) => {
                const na = nodos.find((n) => n.id === a)!;
                const nb = nodos.find((n) => n.id === b)!;
                const p1 = centro(na);
                const p2 = centro(nb);
                return (
                  <path
                    key={`${a}-${b}`}
                    d={`M ${na.x + W} ${p1.y} C ${na.x + W + 40} ${p1.y}, ${nb.x - 40} ${p2.y}, ${nb.x} ${p2.y}`}
                    fill="none"
                    stroke="var(--color-accent)"
                    strokeWidth={1.5}
                    strokeOpacity={0.55}
                  />
                );
              })}
              {nodos.map((n) => (
                <g key={n.id}>
                  <rect
                    x={n.x}
                    y={n.y}
                    width={W}
                    height={H}
                    rx={12}
                    fill="var(--color-background)"
                    stroke="var(--color-border)"
                  />
                  <circle
                    cx={n.x + 14}
                    cy={n.y + 18}
                    r={4}
                    fill={`var(--color-${n.tone === "neutral" ? "muted-foreground" : n.tone})`}
                  />
                  <text
                    x={n.x + 26}
                    y={n.y + 22}
                    fontSize="12"
                    fontWeight="600"
                    fill="var(--color-foreground)"
                  >
                    {n.label}
                  </text>
                  <text
                    x={n.x + 14}
                    y={n.y + 40}
                    fontSize="10.5"
                    fill="var(--color-muted-foreground)"
                  >
                    {n.sub}
                  </text>
                  <text
                    x={n.x + 14}
                    y={n.y + 55}
                    fontSize="10"
                    fill="var(--color-muted-foreground)"
                  >
                    Estado: {n.estado}
                  </text>
                </g>
              ))}
            </svg>
          </div>
          <div className="flex flex-wrap gap-2 border-t border-border px-5 py-3">
            <StatusBadge tone="success">Nodo saludable</StatusBadge>
            <StatusBadge tone="warning">Nodo lento</StatusBadge>
            <StatusBadge tone="neutral">Nodo inactivo</StatusBadge>
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Línea de eventos
          </h2>
          <Rail className="mt-5">
            {eventos.map((e) => (
              <RailItem key={e.t} done={e.done} active={e.activo}>
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                  <p className="min-w-0 truncate text-sm font-semibold">{e.titulo}</p>
                  <span className="mono shrink-0 text-xs text-muted-foreground">{e.t}</span>
                </div>
                <p className="mt-0.5 text-sm text-muted-foreground">{e.detalle}</p>
              </RailItem>
            ))}
          </Rail>
        </section>
      </div>
    </AdminShell>
  );
}
