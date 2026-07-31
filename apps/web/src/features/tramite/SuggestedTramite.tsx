"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Sparkle } from "lucide-react";
import { StatusBadge } from "@/components/nexo/status-badge";
import { listRuns, type RunSummary } from "@/lib/api/client";

const ACTIVE_STATUSES = new Set(["queued", "planning", "running", "waiting_confirmation"]);

function domainLabel(domain: string | null | undefined) {
  if (!domain) return "Trámite";
  return domain.charAt(0).toUpperCase() + domain.slice(1).replaceAll("_", " ");
}

/**
 * Reemplaza la sugerencia fija de la portada por el run activo más reciente.
 * Sin run activo, no se muestra nada: los atajos genéricos ya cubren ese caso.
 */
export function SuggestedTramite() {
  const [run, setRun] = useState<RunSummary | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    void listRuns({ limit: 5 })
      .then((runs) => {
        if (cancelled) return;
        setRun(runs.find((item) => ACTIVE_STATUSES.has(item.status)) ?? null);
      })
      .catch(() => {
        if (!cancelled) setRun(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!run) return null;

  return (
    <section className="rounded-2xl border border-accent/30 bg-accent/8 p-5 shadow-soft">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
        <div className="min-w-0">
          <StatusBadge tone="accent">Trámite en curso</StatusBadge>
          <h2 className="mt-3 text-lg font-bold">{domainLabel(run.domain)}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Trace <span className="mono">{run.trace_id}</span> · continúa donde lo dejaste.
          </p>
        </div>
        <Sparkle className="hidden size-5 shrink-0 text-accent sm:block" />
      </div>
      <div className="mt-4">
        <Link
          href={`/portal/tramite?run_id=${run.run_id}`}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
        >
          Continuar trámite <ArrowRight className="size-4" />
        </Link>
      </div>
    </section>
  );
}
