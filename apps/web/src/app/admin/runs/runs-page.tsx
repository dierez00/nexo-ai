"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Filter, Search, X } from "lucide-react";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { Rail, RailItem } from "@/components/nexo/rail";
import { runs as mockRuns } from "@/lib/mock";
import { cn } from "@/lib/utils";
import { apiFetch, listRuns, type RunEvent, type RunResult, type RunSummary } from "@/lib/api/client";

const ESTADOS: { value: RunResult["status"]; label: string; tone: Tone }[] = [
  { value: "queued", label: "En cola", tone: "info" },
  { value: "planning", label: "Planificando", tone: "info" },
  { value: "running", label: "En curso", tone: "info" },
  { value: "waiting_confirmation", label: "Esperando confirmación", tone: "warning" },
  { value: "succeeded", label: "Completado", tone: "success" },
  { value: "partial", label: "Completado (parcial)", tone: "warning" },
  { value: "failed", label: "Error de herramienta", tone: "destructive" },
  { value: "cancelled", label: "Cancelado", tone: "neutral" },
];

const filtros = ["Todos", ...ESTADOS.map((e) => e.label)];

type Row = {
  id: string;
  trace: string;
  fecha: string;
  dominio: string;
  estado: string;
  tone: Tone;
  latencia: string;
  costo: string;
};

function formatMs(value: number) {
  if (!value) return "—";
  if (value < 1000) return `${Math.round(value)} ms`;
  return `${(value / 1000).toFixed(1)} s`;
}

function toRow(r: RunSummary): Row {
  const meta = ESTADOS.find((e) => e.value === r.status);
  return {
    id: r.run_id,
    trace: r.trace_id,
    fecha: new Date(r.created_at).toLocaleString("es-MX"),
    dominio: r.domain ?? "—",
    estado: meta?.label ?? r.status,
    tone: meta?.tone ?? "neutral",
    latencia: formatMs(r.latency_ms ?? 0),
    costo: r.total_cost_usd != null ? `$${r.total_cost_usd.toFixed(4)}` : "—",
  };
}

function toMockRow(r: (typeof mockRuns)[number]): Row {
  return {
    id: r.id,
    trace: r.trace,
    fecha: r.fecha,
    dominio: r.dominio,
    estado: r.estado,
    tone: r.tone,
    latencia: r.duracion,
    costo: "—",
  };
}

function eventDetail(event: RunEvent) {
  const type = event.type.replaceAll(".", " ");
  if (event.error?.message) return event.error.message;
  if (event.public_data && Object.keys(event.public_data).length > 0) {
    return JSON.stringify(event.public_data);
  }
  return type.charAt(0).toUpperCase() + type.slice(1);
}

export function RunsPage() {
  const [filtro, setFiltro] = useState("Todos");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<string | null>(null);
  const [panel, setPanel] = useState(false);

  const filtroEstado = ESTADOS.find((e) => e.label === filtro)?.value;
  const runsQuery = useQuery({
    queryKey: ["admin", "runs", filtroEstado ?? "todos"],
    queryFn: () => listRuns({ status: filtroEstado, limit: 50 }),
  });

  const usingFallback = Boolean(runsQuery.error);
  const rows = usingFallback
    ? mockRuns.map(toMockRow).filter((r) => filtro === "Todos" || r.estado === filtro)
    : (runsQuery.data ?? []).map(toRow);

  const needle = q.trim().toLowerCase();
  const lista = needle
    ? rows.filter((r) => r.trace.toLowerCase().includes(needle) || r.dominio.toLowerCase().includes(needle))
    : rows;

  const selRow = lista.find((r) => r.id === sel) ?? null;
  const runDetail = useQuery({
    queryKey: ["admin", "runs", sel],
    queryFn: () => apiFetch<RunResult>(`/api/v1/runs/${sel}`),
    enabled: Boolean(sel) && !usingFallback,
  });
  const runEvents = useQuery({
    queryKey: ["admin", "runs", sel, "events"],
    queryFn: () => apiFetch<RunEvent[]>(`/api/v1/runs/${sel}/events/list`),
    enabled: Boolean(sel) && !usingFallback,
  });

  return (
    <AdminShell
      title="Runs"
      subtitle={`${lista.length} ejecuciones en el rango seleccionado`}
      actions={
        <div className="flex items-center gap-2">
          <StatusBadge tone={usingFallback ? "warning" : "success"}>
            {usingFallback ? "Mostrando fallback" : "API conectada"}
          </StatusBadge>
          <button
            onClick={() => setPanel(true)}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-medium lg:hidden"
          >
            <Filter className="size-3.5" /> Filtros
          </button>
        </div>
      }
    >
      <div className="mb-4 grid gap-3 rounded-2xl border border-border bg-card p-4 shadow-soft lg:grid-cols-[minmax(0,1fr)_auto]">
        <label className="flex min-w-0 items-center gap-2 rounded-full border border-border bg-background px-4 py-2">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar por trace id o dominio"
            className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </label>
        <div className="hidden flex-wrap gap-2 lg:flex">
          {filtros.map((f) => (
            <button
              key={f}
              onClick={() => setFiltro(f)}
              className={cn(
                "rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
                filtro === f
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        {/* Tabla en escritorio */}
        <div className="hidden overflow-hidden rounded-2xl border border-border bg-card shadow-soft md:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Dominio</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Latencia</th>
                <th className="px-4 py-3 font-medium">Trace id</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => setSel(r.id)}
                  className={cn(
                    "cursor-pointer border-t border-border transition-colors hover:bg-secondary/60",
                    sel === r.id && "bg-secondary",
                  )}
                >
                  <td className="mono whitespace-nowrap px-4 py-3 text-xs">{r.fecha}</td>
                  <td className="px-4 py-3">{r.dominio}</td>
                  <td className="px-4 py-3">
                    <StatusBadge tone={r.tone}>{r.estado}</StatusBadge>
                  </td>
                  <td className="mono px-4 py-3 text-xs text-muted-foreground">{r.latencia}</td>
                  <td className="mono px-4 py-3 text-xs text-muted-foreground">{r.trace}</td>
                </tr>
              ))}
              {lista.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-sm text-muted-foreground">
                    No hay ejecuciones para este filtro.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        {/* Tarjetas apiladas en móvil */}
        <ul className="space-y-3 md:hidden">
          {lista.map((r) => (
            <li key={r.id}>
              <button
                onClick={() => setSel(r.id)}
                className="w-full rounded-2xl border border-border bg-card p-4 text-left shadow-soft"
              >
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                  <p className="truncate text-sm font-semibold">{r.dominio}</p>
                  <StatusBadge tone={r.tone}>{r.estado}</StatusBadge>
                </div>
                <dl className="mt-3 space-y-1 text-xs">
                  {[
                    ["Fecha", r.fecha],
                    ["Latencia", r.latencia],
                    ["Trace id", r.trace],
                  ].map(([k, v]) => (
                    <div key={k} className="grid grid-cols-[88px_minmax(0,1fr)] gap-2">
                      <dt className="text-muted-foreground">{k}</dt>
                      <dd className="mono truncate">{v}</dd>
                    </div>
                  ))}
                </dl>
              </button>
            </li>
          ))}
        </ul>

        <aside className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          {selRow ? (
            <>
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                <div className="min-w-0">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">
                    Detalle del run
                  </p>
                  <p className="mono mt-1 truncate text-base font-semibold">{selRow.id}</p>
                </div>
                <button
                  onClick={() => setSel(null)}
                  aria-label="Cerrar detalle"
                  className="rounded-full border border-border p-1.5 text-muted-foreground"
                >
                  <X className="size-3.5" />
                </button>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <StatusBadge tone={selRow.tone}>{selRow.estado}</StatusBadge>
              </div>
              <dl className="mt-5 space-y-2 text-sm">
                {[
                  ["Dominio", selRow.dominio],
                  ["Latencia", selRow.latencia],
                  ["Costo", selRow.costo],
                  ["Trace id", selRow.trace],
                ].map(([k, v]) => (
                  <div key={k} className="grid grid-cols-[120px_minmax(0,1fr)] gap-3">
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="mono truncate">{v}</dd>
                  </div>
                ))}
              </dl>
              <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Trazabilidad
              </h3>
              {usingFallback ? (
                <p className="mt-4 text-sm text-muted-foreground">
                  Datos de ejemplo; conecta la API para ver la traza real de eventos.
                </p>
              ) : runEvents.data && runEvents.data.length > 0 ? (
                <Rail className="mt-4">
                  {runEvents.data.map((event, index) => (
                    <RailItem
                      key={event.event_id}
                      done={index < runEvents.data!.length - 1}
                      active={index === runEvents.data!.length - 1}
                    >
                      <p className="text-sm font-semibold">{event.type}</p>
                      <p className="text-sm text-muted-foreground">{eventDetail(event)}</p>
                    </RailItem>
                  ))}
                </Rail>
              ) : (
                <p className="mt-4 text-sm text-muted-foreground">
                  {runEvents.isLoading ? "Cargando eventos…" : "Sin eventos registrados."}
                </p>
              )}
              {!usingFallback && runDetail.data?.answer ? (
                <p className="mt-6 rounded-xl bg-muted/60 p-3 text-sm text-muted-foreground">
                  {runDetail.data.answer}
                </p>
              ) : null}
            </>
          ) : (
            <div className="flex h-full min-h-56 flex-col items-center justify-center text-center">
              <p className="text-sm font-semibold">Selecciona una ejecución</p>
              <p className="mt-1 max-w-xs text-sm text-muted-foreground">
                Al hacer clic en una fila verás sus pasos, herramientas y trazabilidad.
              </p>
            </div>
          )}
        </aside>
      </div>

      {panel ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Cerrar filtros"
            className="absolute inset-0 bg-foreground/40"
            onClick={() => setPanel(false)}
          />
          <div className="absolute inset-x-0 bottom-0 rounded-t-2xl border-t border-border bg-card p-5">
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
              <h2 className="text-sm font-semibold">Filtrar por estado</h2>
              <button onClick={() => setPanel(false)} aria-label="Cerrar filtros">
                <X className="size-4 text-muted-foreground" />
              </button>
            </div>
            <ul className="mt-4 space-y-2">
              {filtros.map((f) => (
                <li key={f}>
                  <button
                    onClick={() => {
                      setFiltro(f);
                      setPanel(false);
                    }}
                    className={cn(
                      "w-full rounded-xl border px-4 py-2.5 text-left text-sm",
                      filtro === f ? "border-accent bg-accent/10 font-medium" : "border-border",
                    )}
                  >
                    {f}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </AdminShell>
  );
}
