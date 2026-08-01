import { Rail, RailItem } from "@/components/nexo/rail";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import type { Phase, PhaseState } from "./run-phases";

const STATE_TONE: Record<PhaseState, Tone> = {
  pendiente: "neutral",
  en_curso: "info",
  completado: "success",
  fallido: "destructive",
};

const STATE_LABEL: Record<PhaseState, string> = {
  pendiente: "Pendiente",
  en_curso: "En curso",
  completado: "Completado",
  fallido: "Con error",
};

/** Línea de tiempo del run, en fases legibles y no en tipos de evento. */
export function ChatTimeline({ fases }: { fases: Phase[] }) {
  if (fases.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Línea de tiempo
      </p>
      <Rail>
        {fases.map((fase) => (
          <RailItem
            key={fase.id}
            done={fase.state === "completado"}
            active={fase.state === "en_curso"}
          >
            <p className="text-sm font-semibold">{fase.label}</p>
            <p className="mt-0.5 text-sm text-muted-foreground">{fase.detail}</p>
            <StatusBadge tone={STATE_TONE[fase.state]} className="mt-2">
              {STATE_LABEL[fase.state]}
            </StatusBadge>
          </RailItem>
        ))}
      </Rail>
    </div>
  );
}

export function ProgressSteps({
  paso,
  total,
  label,
}: {
  paso: number;
  total: number;
  label: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">{label}</p>
        <span className="mono shrink-0 text-xs text-muted-foreground">
          Paso {paso} de {total}
        </span>
      </div>
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-accent transition-all"
          style={{ width: `${(paso / total) * 100}%` }}
        />
      </div>
    </div>
  );
}
