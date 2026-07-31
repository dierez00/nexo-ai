"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, Copy, ExternalLink, FileText, LifeBuoy, RefreshCw } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { Rail, RailItem } from "@/components/nexo/rail";
import { useActiveRun } from "@/features/tramite/useActiveRun";
import { readFolioFor } from "@/features/tramite/folio-history";
import type { RunEvent, RunResult } from "@/generated/contracts";

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

function eventDetail(event: RunEvent) {
  const type = event.type.replaceAll(".", " ");
  if (event.error?.message) return event.error.message;
  if (event.public_data && Object.keys(event.public_data).length > 0) {
    return JSON.stringify(event.public_data);
  }
  return type.charAt(0).toUpperCase() + type.slice(1);
}

export function SeguimientoPage() {
  const searchParams = useSearchParams();
  const runIdParam = searchParams.get("run_id");
  const { state, retry } = useActiveRun(runIdParam);

  if (state.status === "loading") {
    return (
      <PortalShell title="Seguimiento">
        <div className="space-y-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-2xl border border-border bg-card" />
          ))}
        </div>
      </PortalShell>
    );
  }

  if (state.status === "empty") {
    return (
      <PortalShell title="Seguimiento">
        <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center shadow-soft">
          <FileText className="mx-auto size-6 text-muted-foreground" />
          <p className="mt-3 text-lg font-semibold">Todavía no tienes trámites que seguir</p>
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
      <PortalShell title="Seguimiento">
        <div className="rounded-2xl border border-destructive/35 bg-destructive/8 p-6 shadow-soft">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="size-5" />
            <h2 className="text-base font-semibold">No pudimos cargar el seguimiento</h2>
          </div>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">{state.message}</p>
          <button
            onClick={retry}
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground"
          >
            <RefreshCw className="size-4" /> Volver a intentar
          </button>
        </div>
      </PortalShell>
    );
  }

  const { run, events } = state;
  const folio = readFolioFor(run.run_id);
  const { label, tone } = STATUS_LABEL[run.status];

  return (
    <PortalShell title="Seguimiento" subtitle={folio ? `Folio ${folio.folio}` : `Trace ${run.trace_id}`}>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div className="space-y-4">
          <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
              <div className="min-w-0">
                <p className="text-sm text-muted-foreground">Trace del trámite</p>
                <p className="mono mt-1 truncate text-xl font-semibold">{run.trace_id}</p>
              </div>
              {folio ? (
                <button
                  onClick={() => void navigator.clipboard?.writeText(folio.folio)}
                  className="inline-flex shrink-0 items-center gap-2 rounded-full border border-border px-3 py-1.5 text-xs font-medium"
                >
                  <Copy className="size-3.5" /> Copiar folio
                </button>
              ) : null}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <StatusBadge tone={tone}>{label}</StatusBadge>
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Línea de tiempo
            </h2>
            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aún no hay eventos registrados.</p>
            ) : (
              <Rail>
                {events.map((event, index) => (
                  <RailItem key={event.event_id} done={index < events.length - 1} active={index === events.length - 1}>
                    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                      <p className="min-w-0 text-sm font-semibold">{event.type}</p>
                      <span className="mono shrink-0 text-xs text-muted-foreground">
                        {new Date(event.timestamp).toLocaleString("es-BO")}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{eventDetail(event)}</p>
                  </RailItem>
                ))}
              </Rail>
            )}
          </section>
        </div>

        <div className="space-y-4 lg:sticky lg:top-24 lg:h-fit">
          {run.status === "waiting_confirmation" ? (
            <section className="rounded-2xl border border-accent/35 bg-accent/8 p-5 shadow-soft">
              <StatusBadge tone="accent">Próxima acción</StatusBadge>
              <h2 className="mt-3 text-lg font-bold">Tienes una confirmación pendiente</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Vuelve al chat para revisar los detalles y confirmar.
              </p>
              <Link
                href="/portal/chat"
                className="mt-4 inline-flex w-full items-center justify-center rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
              >
                Ir al chat
              </Link>
            </section>
          ) : null}

          {run.sources?.length ? (
            <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Fuentes citadas
              </h2>
              <ul className="space-y-2">
                {run.sources.map((source) => (
                  <li key={`${source.source_id}-${source.fragment_id}`} className="text-sm">
                    <span className="mono">{source.source_id}</span>{" "}
                    <ExternalLink className="inline size-3 text-muted-foreground" />
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="flex items-center gap-2">
              <LifeBuoy className="size-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold">¿Necesitas ayuda?</h2>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Un orientador puede revisar tu caso contigo, de lunes a viernes de 08:00 a 17:00.
            </p>
            <Link
              href="/agente-voz"
              className="mt-4 inline-flex w-full items-center justify-center rounded-full border border-border px-6 py-2.5 text-sm font-semibold transition-colors hover:bg-secondary"
            >
              Llamar al agente
            </Link>
            <Link
              href="/portal/chat"
              className="mt-2 inline-flex w-full items-center justify-center rounded-full border border-border px-6 py-2.5 text-sm font-semibold transition-colors hover:bg-secondary"
            >
              Escribir por chat
            </Link>
          </section>
        </div>
      </div>
    </PortalShell>
  );
}
