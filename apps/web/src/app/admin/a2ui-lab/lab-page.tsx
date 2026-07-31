"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, Play, ShieldAlert, ShieldCheck } from "lucide-react";

import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { A2UIFallback } from "@/features/a2ui/Fallback";
import { A2UISurface } from "@/features/a2ui/Surface";
import { CITIZEN_CATALOG_ID } from "@/features/a2ui/catalog";
import {
  aggregate,
  afterPaint,
  round,
  type Aggregate,
  type Sample,
} from "@/features/a2ui/instrumentation";
import { processJsonl } from "@/features/a2ui/processor";
import type { ProcessResult, Surface } from "@/features/a2ui/types";
import { cn } from "@/lib/utils";

type ManifestEntry = {
  name: string;
  valid: boolean;
  components?: number;
  facts?: number;
  rule?: string;
  bytes: number;
};

type ServerTimings = {
  generated_at: string;
  note: string;
  by_size: Record<
    string,
    { runs: number; build_p50_ms: number; validate_p50_ms: number; total_p50_ms: number }
  >;
};

/** Acción declarada por los fixtures válidos; el banco no habla con el backend. */
const DECLARED_ACTIONS = [{ actionId: "act_reserve_01", label: "Reservar cita" }];

const RUNS = 20;

export function A2UILab() {
  const [manifest, setManifest] = useState<ManifestEntry[]>([]);
  const [serverTimings, setServerTimings] = useState<ServerTimings | null>(null);
  const [selected, setSelected] = useState<string>("valid__catalog");
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [lastSample, setLastSample] = useState<Sample | null>(null);
  const [summary, setSummary] = useState<Aggregate | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    void Promise.all([
      fetch("/fixtures/a2ui/manifest.json").then((r) => r.json() as Promise<ManifestEntry[]>),
      fetch("/fixtures/a2ui/timings.json").then((r) => r.json() as Promise<ServerTimings>),
    ]).then(([entries, timings]) => {
      setManifest(entries);
      setServerTimings(timings);
    });
  }, []);

  const load = useCallback(async (name: string): Promise<Sample | null> => {
    const start = performance.now();
    const response = await fetch(`/fixtures/a2ui/${name}.jsonl`, { cache: "no-store" });
    const text = await response.text();
    const transportMs = performance.now() - start;

    const processed = processJsonl(text, DECLARED_ACTIONS);

    const beforeCommit = performance.now();
    setResult(processed);
    const painted = await afterPaint();

    return {
      transportMs,
      parseMs: processed.timings.parseMs,
      guardMs: processed.timings.guardMs,
      renderMs: painted - beforeCommit,
      totalMs: painted - start,
    };
  }, []);

  // La carga arranca fuera del cuerpo del efecto: `load` pinta la superficie
  // para poder medir su commit, y hacerlo en línea encadenaría renders. El
  // resumen se limpia al elegir fixture, no aquí.
  useEffect(() => {
    void Promise.resolve()
      .then(() => load(selected))
      .then(setLastSample);
  }, [selected, load]);

  const selectFixture = useCallback((name: string) => {
    setSummary(null);
    setSelected(name);
  }, []);

  const sweep = useCallback(async () => {
    setRunning(true);
    const samples: Sample[] = [];
    for (let index = 0; index < RUNS; index += 1) {
      const sample = await load(selected);
      if (sample) samples.push(sample);
    }
    setSummary(aggregate(samples));
    setRunning(false);
  }, [load, selected]);

  const exportJson = useCallback(() => {
    const payload = {
      fixture: selected,
      generated_at: new Date().toISOString(),
      catalog_id: CITIZEN_CATALOG_ID,
      server: serverTimings?.by_size[selected] ?? null,
      client: summary,
      blocked: {
        model: "no hay orquestación: el modelo produce VerifiedFacts aguas arriba",
        sse: "RunResult todavía no lleva la superficie",
      },
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `a2ui-${selected}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [selected, summary, serverTimings]);

  const entry = manifest.find((item) => item.name === selected);
  const server = serverTimings?.by_size[selected];

  return (
    <AdminShell
      title="Banco A2UI"
      subtitle="Renderer del catálogo ciudadano y línea de tiempo hasta la primera superficie."
      actions={
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void sweep()}
            disabled={running}
            className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Play className="size-4" aria-hidden />
            {running ? `Corriendo ${RUNS}…` : `Correr ${RUNS} veces`}
          </button>
          <button
            type="button"
            onClick={exportJson}
            disabled={!summary}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm font-semibold transition-colors hover:bg-secondary disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Download className="size-4" aria-hidden /> Exportar
          </button>
        </div>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <div className="space-y-6">
          <section className="rounded-2xl border border-border bg-card p-4 shadow-soft">
            <h2 className="text-sm font-semibold">Fixtures</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Generados por el builder real y validados antes de escribirse.
            </p>
            <ul className="mt-3 space-y-1">
              {manifest.map((item) => (
                <li key={item.name}>
                  <button
                    type="button"
                    onClick={() => selectFixture(item.name)}
                    className={cn(
                      "grid w-full grid-cols-[auto_minmax(0,1fr)] items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      selected === item.name
                        ? "bg-secondary text-secondary-foreground"
                        : "hover:bg-secondary/60",
                    )}
                  >
                    {item.valid ? (
                      <ShieldCheck className="size-3.5 shrink-0 text-success" aria-hidden />
                    ) : (
                      <ShieldAlert className="size-3.5 shrink-0 text-destructive" aria-hidden />
                    )}
                    <span className="mono truncate text-xs">{item.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <TimelineCard entry={entry} server={server} sample={lastSample} summary={summary} />
        </div>

        <section className="space-y-4">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
            <div className="min-w-0">
              <h2 className="text-sm font-semibold">Superficie renderizada</h2>
              <p className="mono mt-0.5 truncate text-xs text-muted-foreground">{selected}</p>
            </div>
            {result ? (
              <StatusBadge tone={result.ok ? "success" : "destructive"}>
                {result.ok ? "Aceptada" : "Rechazada"}
              </StatusBadge>
            ) : null}
          </div>

          <div className="rounded-2xl border border-border bg-background p-4 sm:p-6">
            {result === null ? (
              <p className="text-sm text-muted-foreground">Cargando fixture…</p>
            ) : result.ok ? (
              <A2UISurface surface={result.surface as Surface} traceId="trc_lab_local" />
            ) : (
              <A2UIFallback traceId="trc_lab_local" />
            )}
          </div>

          {result && !result.ok ? (
            <div className="rounded-xl border border-border bg-card p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Reglas violadas
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Se reporta la regla, nunca el valor que la violó.
              </p>
              <ul className="mt-3 space-y-2">
                {result.errors.map((error, index) => (
                  <li key={`${error.rule}-${index}`} className="text-sm">
                    <span className="mono text-xs font-semibold text-destructive">
                      {error.rule}
                    </span>
                    {error.componentId ? (
                      <span className="mono ml-2 text-xs text-muted-foreground">
                        #{error.componentId}
                      </span>
                    ) : null}
                    <p className="text-sm text-muted-foreground">{error.detail}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      </div>
    </AdminShell>
  );
}

function Row({
  label,
  value,
  blocked,
  emphasis = false,
}: {
  label: string;
  value?: string;
  blocked?: string;
  emphasis?: boolean;
}) {
  return (
    <li
      className={cn(
        "grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-3 py-1.5",
        emphasis && "border-t border-border pt-2 font-semibold",
      )}
    >
      <span className={cn("min-w-0 text-sm", blocked && "text-muted-foreground")}>{label}</span>
      {blocked ? (
        <span className="shrink-0 text-xs text-muted-foreground">bloqueado</span>
      ) : (
        <span className="mono shrink-0 text-sm">{value ?? "—"}</span>
      )}
    </li>
  );
}

function TimelineCard({
  entry,
  server,
  sample,
  summary,
}: {
  entry?: ManifestEntry;
  server?: { build_p50_ms: number; validate_p50_ms: number; total_p50_ms: number };
  sample: Sample | null;
  summary: Aggregate | null;
}) {
  const show = (last: number | undefined, p50: number | undefined) => {
    if (summary && p50 !== undefined) return `${p50} ms`;
    if (last !== undefined) return `${round(last)} ms`;
    return "—";
  };

  return (
    <section className="rounded-2xl border border-border bg-card p-4 shadow-soft">
      <h2 className="text-sm font-semibold">Time-to-first-surface</h2>
      <p className="mt-1 text-xs text-muted-foreground">
        {summary ? `p50 de ${summary.runs} corridas` : "última corrida"}
        {entry ? ` · ${entry.bytes} B` : ""}
        {entry?.components ? ` · ${entry.components} componentes` : ""}
      </p>

      <ul className="mt-3">
        <Row label="1 · modelo → hechos" blocked="sin orquestación" />
        <Row label="2 · builder + validator" value={server ? `${server.total_p50_ms} ms` : "—"} />
        <Row label="3 · SSE → navegador" blocked="RunResult sin superficie" />
        <Row
          label="4 · fetch del fixture"
          value={show(sample?.transportMs, summary?.transport.p50)}
        />
        <Row label="5 · parseo JSONL" value={show(sample?.parseMs, summary?.parse.p50)} />
        <Row label="6 · guard + lifecycle" value={show(sample?.guardMs, summary?.guard.p50)} />
        <Row
          label="7 · commit + primer frame"
          value={show(sample?.renderMs, summary?.render.p50)}
        />
        <Row label="Total cliente" value={show(sample?.totalMs, summary?.total.p50)} emphasis />
      </ul>

      {summary ? (
        <p className="mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
          p95 total: <span className="mono">{summary.total.p95} ms</span>
        </p>
      ) : null}

      <p className="mt-3 text-xs text-muted-foreground">
        Los tramos 1 y 3 dependen de que la orquestación emita la superficie por el run. La tabla
        los deja declarados para que al conectarse solo cambie la fuente de datos.
      </p>
      <p className="mt-2 text-xs text-muted-foreground">
        El tramo 7 no puede bajar de lo que falte para el siguiente frame (~16 ms a 60 Hz). Si marca
        cerca de ese piso, el commit no está costando nada: es la espera.
      </p>
    </section>
  );
}
