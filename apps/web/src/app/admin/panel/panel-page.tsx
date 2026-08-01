"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3, Clock, Play, RefreshCw } from "lucide-react";

import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { buildMockAdminChartSurface } from "@/features/a2ui/admin-mock";
import { SurfaceFromRun } from "@/features/a2ui/SurfaceFromRun";
import { cn } from "@/lib/utils";

const EXAMPLES = [
  "trámites por dominio en 30 días",
  "tendencia de trámites diaria",
  "runs por estado",
  "latencia y costo",
  "acciones por estado",
  "citas por estado",
  "conversaciones",
];

const RANGES = [
  { label: "7 días", days: 7 },
  { label: "30 días", days: 30 },
  { label: "90 días", days: 90 },
];

export function AdminPanelPage() {
  const [prompt, setPrompt] = useState(EXAMPLES[0]);
  const [submittedPrompt, setSubmittedPrompt] = useState(EXAMPLES[0]);
  const [rangeDays, setRangeDays] = useState(30);
  const [isGenerating, setIsGenerating] = useState(true);
  const [generationKey, setGenerationKey] = useState(0);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setIsGenerating(false);
      setUpdatedAt(new Date().toLocaleTimeString("es-MX"));
    }, 1100);
    return () => window.clearTimeout(timeout);
  }, [generationKey]);

  const surface = useMemo(
    () => buildMockAdminChartSurface(submittedPrompt, rangeDays),
    [submittedPrompt, rangeDays],
  );
  function requestGeneration(nextPrompt = prompt, nextRangeDays = rangeDays) {
    setPrompt(nextPrompt);
    setSubmittedPrompt(nextPrompt.trim() || EXAMPLES[0]);
    setRangeDays(nextRangeDays);
    setIsGenerating(true);
    setGenerationKey((value) => value + 1);
  }

  return (
    <AdminShell
      title="Panel admin"
      subtitle="Gráficas administrativas generadas como superficies A2UI validadas."
      actions={
        <div className="flex flex-wrap items-center justify-end gap-2">
          <StatusBadge tone={isGenerating ? "info" : "success"}>
            {isGenerating ? "Generando" : "Listo"}
          </StatusBadge>
        </div>
      }
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(19rem,24rem)_minmax(0,1fr)]">
        <aside className="space-y-4">
          <section className="rail rounded-xl border border-border bg-card p-4 shadow-soft">
            <span aria-hidden className="rail-node" />
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <BarChart3 className="size-4" aria-hidden />
              Solicitud
            </div>
            <form
              className="mt-3 space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                requestGeneration();
              }}
            >
              <label className="block text-sm font-medium" htmlFor="admin-chart-prompt">
                Qué quieres ver
              </label>
              <textarea
                id="admin-chart-prompt"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                rows={5}
                maxLength={500}
                className="min-h-32 w-full resize-y rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Ej. trámites por dominio en 30 días"
              />
              <button
                type="submit"
                disabled={isGenerating}
                className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {isGenerating ? (
                  <RefreshCw className="size-4 animate-spin" aria-hidden />
                ) : (
                  <Play className="size-4" aria-hidden />
                )}
                Generar gráfica
              </button>
            </form>
          </section>

          <section className="rounded-xl border border-border bg-card p-4 shadow-soft">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <Clock className="size-4" aria-hidden />
              Rango
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2">
              {RANGES.map((range) => (
                <button
                  key={range.days}
                  type="button"
                  onClick={() => requestGeneration(prompt, range.days)}
                  className={cn(
                    "min-h-10 rounded-full border px-2 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    rangeDays === range.days
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border text-muted-foreground hover:text-foreground",
                  )}
                >
                  {range.label}
                </button>
              ))}
            </div>
            <div className="mt-4 space-y-2">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => requestGeneration(example, rangeDays)}
                  className="w-full rounded-lg px-2 py-1.5 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {example}
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="min-w-0 space-y-4">
          <div className="grid gap-3 rounded-xl border border-border bg-card p-4 shadow-soft md:grid-cols-[minmax(0,1fr)_auto]">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Superficie generada
              </p>
              <p className="mt-1 truncate text-sm">{submittedPrompt}</p>
            </div>
            <div className="mono text-xs text-muted-foreground">
              {updatedAt ? `Actualizado ${updatedAt}` : "Preparando"}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-background p-4 sm:p-5">
            {isGenerating ? (
              <ChartLoading />
            ) : (
              <SurfaceFromRun surface={surface} traceId="trace_admin_panel" />
            )}
          </div>
        </section>
      </div>
    </AdminShell>
  );
}

function ChartLoading() {
  return (
    <div className="grid min-h-[34rem] place-items-center rounded-xl border border-border bg-card p-6">
      <div className="w-full max-w-3xl">
        <div className="mx-auto grid size-14 place-items-center rounded-full border border-info/30 bg-info/10 text-info">
          <RefreshCw className="size-6 animate-spin" aria-hidden />
        </div>
        <div className="mt-5 text-center">
          <p className="text-base font-semibold">Construyendo gráfica personalizada</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Interpretando solicitud, preparando agregados y validando la superficie A2UI.
          </p>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {["Interpretación", "Agregación", "Render A2UI"].map((label, index) => (
            <div key={label} className="rounded-xl border border-border bg-background p-4">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "size-2 rounded-full",
                    index === 0 && "bg-info",
                    index === 1 && "bg-accent",
                    index === 2 && "bg-success",
                  )}
                />
                <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {label}
                </span>
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className={cn(
                    "h-full rounded-full",
                    index === 0 && "w-11/12 bg-info",
                    index === 1 && "w-2/3 bg-accent",
                    index === 2 && "w-1/2 bg-success",
                  )}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 h-72 rounded-xl border border-border bg-background p-4">
          <div className="flex h-full items-end gap-3">
            {[42, 78, 55, 92, 66, 84, 48, 73, 61].map((height, index) => (
              <div key={index} className="flex flex-1 flex-col justify-end">
                <div
                  className="rounded-t-lg bg-gradient-to-t from-accent/75 to-info/70"
                  style={{ height: `${height}%` }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
