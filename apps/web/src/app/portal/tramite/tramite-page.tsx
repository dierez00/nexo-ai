"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, ExternalLink, FileText, RefreshCw } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { SurfaceFromRun } from "@/features/a2ui/SurfaceFromRun";
import { useActiveRun } from "@/features/tramite/useActiveRun";
import { readFolioFor } from "@/features/tramite/folio-history";
import type { RunResult } from "@/generated/contracts";

const STATUS_LABEL: Record<RunResult["status"], { label: string; tone: Tone }> = {
  queued: { label: "Pendiente", tone: "info" },
  planning: { label: "Pendiente", tone: "info" },
  running: { label: "Ejecutando", tone: "info" },
  waiting_confirmation: { label: "Esperando tu confirmación", tone: "warning" },
  succeeded: { label: "Completado", tone: "success" },
  partial: { label: "Completado con datos parciales", tone: "warning" },
  failed: { label: "Fallido", tone: "destructive" },
  cancelled: { label: "Cancelado", tone: "neutral" },
};

export function TramitePage() {
  const searchParams = useSearchParams();
  const runIdParam = searchParams.get("run_id");
  const { state, retry } = useActiveRun(runIdParam);

  if (state.status === "loading") {
    return (
      <PortalShell title="Tu trámite">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          {[0, 1].map((c) => (
            <div key={c} className="space-y-4">
              {[0, 1].map((i) => (
                <div key={i} className="space-y-3 rounded-2xl border border-border bg-card p-5">
                  <div className="h-3 w-32 animate-pulse rounded-full bg-muted" />
                  <div className="h-3 w-full animate-pulse rounded-full bg-muted" />
                  <div className="h-3 w-4/5 animate-pulse rounded-full bg-muted" />
                </div>
              ))}
            </div>
          ))}
        </div>
      </PortalShell>
    );
  }

  if (state.status === "empty") {
    return (
      <PortalShell title="Tu trámite">
        <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center shadow-soft">
          <FileText className="mx-auto size-6 text-muted-foreground" />
          <p className="mt-3 text-lg font-semibold">Todavía no tienes trámites abiertos</p>
          <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
            Cuando inicies un trámite verás aquí su estado, requisitos y costos. Puedes empezar
            preguntando al asistente.
          </p>
          <Link
            href="/portal/chat"
            className="mt-5 inline-flex rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground"
          >
            Iniciar un trámite
          </Link>
        </div>
      </PortalShell>
    );
  }

  if (state.status === "error") {
    return (
      <PortalShell title="Tu trámite">
        <div className="rounded-2xl border border-destructive/35 bg-destructive/8 p-6 shadow-soft">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="size-5" />
            <h2 className="text-base font-semibold">No pudimos cargar tu trámite</h2>
          </div>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">{state.message}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            <button
              onClick={retry}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground"
            >
              <RefreshCw className="size-4" /> Volver a intentar
            </button>
            <Link
              href="/portal/chat"
              className="rounded-full border border-border bg-card px-5 py-2.5 text-sm font-semibold"
            >
              Avisar al asistente
            </Link>
          </div>
        </div>
      </PortalShell>
    );
  }

  const { run } = state;
  const folio = readFolioFor(run.run_id);
  const { label, tone } = STATUS_LABEL[run.status];
  const partial = run.status === "partial" || run.warnings?.length;

  return (
    <PortalShell
      title="Tu trámite"
      subtitle={folio ? `Folio ${folio.folio} · trace ${run.trace_id}` : `Trace ${run.trace_id}`}
    >
      <div className="mb-5 flex flex-wrap gap-2">
        <StatusBadge tone={tone}>{label}</StatusBadge>
      </div>

      {partial && run.warnings?.length ? (
        <div className="mb-4 rounded-2xl border border-warning/40 bg-warning/10 p-5 shadow-soft">
          <StatusBadge tone="warning">Mostrando datos parciales</StatusBadge>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {run.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {run.status === "failed" && run.error ? (
        <div className="rounded-2xl border border-destructive/35 bg-destructive/8 p-6 shadow-soft">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="size-5" />
            <h2 className="text-base font-semibold">{run.error.message}</h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            Tus documentos ya cargados están a salvo y ningún plazo se ve afectado.
          </p>
          <Link
            href="/portal/chat"
            className="mt-5 inline-flex rounded-full border border-border bg-card px-5 py-2.5 text-sm font-semibold"
          >
            Avisar al asistente
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          <div className="space-y-4">
            {run.surface ? (
              <SurfaceFromRun surface={run.surface} traceId={run.trace_id} />
            ) : (
              <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
                <p className="text-sm leading-relaxed">
                  {run.answer || run.fallback?.text || "Sin respuesta textual todavía."}
                </p>
              </section>
            )}
          </div>

          {run.sources?.length ? (
            <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Fuentes oficiales citadas
              </h2>
              <ul className="space-y-3">
                {run.sources.map((source) => (
                  <li key={`${source.source_id}-${source.fragment_id}`} className="rail">
                    <span aria-hidden className="rail-node bg-accent" />
                    <p className="mono text-sm font-medium">{source.source_id}</p>
                    <p className="mono text-xs text-muted-foreground">
                      Corpus {source.corpus_version}
                    </p>
                    <span className="mt-1 inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                      Fragmento {source.fragment_id} <ExternalLink className="size-3" />
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      )}
    </PortalShell>
  );
}
