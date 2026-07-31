"use client";

import { useState } from "react";
import { Filter, Search, X } from "lucide-react";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { Rail, RailItem } from "@/components/nexo/rail";
import { runs } from "@/lib/mock";
import { cn } from "@/lib/utils";

const filtros = ["Todos", "Completado", "En curso", "Error de herramienta", "Derivado a humano"];

export function RunsPage() {
  const [filtro, setFiltro] = useState("Todos");
  const [sel, setSel] = useState<string | null>(null);
  const [panel, setPanel] = useState(false);

  const lista = filtro === "Todos" ? runs : runs.filter((r) => r.estado === filtro);
  const run = runs.find((r) => r.id === sel) ?? null;

  return (
    <AdminShell
      title="Runs"
      subtitle={`${lista.length} ejecuciones en el rango seleccionado`}
      actions={
        <button
          onClick={() => setPanel(true)}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-medium lg:hidden"
        >
          <Filter className="size-3.5" /> Filtros
        </button>
      }
    >
      <div className="mb-4 grid gap-3 rounded-2xl border border-border bg-card p-4 shadow-soft lg:grid-cols-[minmax(0,1fr)_auto]">
        <label className="flex min-w-0 items-center gap-2 rounded-full border border-border bg-background px-4 py-2">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            placeholder="Buscar por trace id, folio o dominio"
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
                <th className="px-4 py-3 font-medium">Canal</th>
                <th className="px-4 py-3 font-medium">Estado</th>
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
                  <td className="px-4 py-3 text-muted-foreground">{r.canal}</td>
                  <td className="px-4 py-3">
                    <StatusBadge tone={r.tone}>{r.estado}</StatusBadge>
                  </td>
                  <td className="mono px-4 py-3 text-xs text-muted-foreground">{r.trace}</td>
                </tr>
              ))}
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
                    ["Canal", r.canal],
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
          {run ? (
            <>
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                <div className="min-w-0">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">
                    Detalle del run
                  </p>
                  <p className="mono mt-1 truncate text-base font-semibold">{run.id}</p>
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
                <StatusBadge tone={run.tone}>{run.estado}</StatusBadge>
                <StatusBadge tone="info">{run.canal}</StatusBadge>
              </div>
              <dl className="mt-5 space-y-2 text-sm">
                {[
                  ["Dominio", run.dominio],
                  ["Duración", run.duracion],
                  ["Pasos ejecutados", String(run.pasos)],
                  ["Trace id", run.trace],
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
              <Rail className="mt-4">
                <RailItem done>
                  <p className="text-sm font-semibold">Estado</p>
                  <p className="text-sm text-muted-foreground">
                    Intención clasificada: {run.dominio.toLowerCase()}.
                  </p>
                </RailItem>
                <RailItem done>
                  <p className="text-sm font-semibold">Fuente</p>
                  <p className="text-sm text-muted-foreground">
                    Herramienta <span className="mono">consultar_requisitos</span> · 320 ms
                  </p>
                </RailItem>
                <RailItem active>
                  <p className="text-sm font-semibold">Siguiente acción</p>
                  <p className="text-sm text-muted-foreground">
                    Respuesta entregada con checklist y fuente citada.
                  </p>
                </RailItem>
              </Rail>
              <button className="mt-6 w-full rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground">
                Abrir traza completa
              </button>
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
