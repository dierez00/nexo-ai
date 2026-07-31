import { AlertTriangle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

export function QuickActions({ acciones }: { acciones: { texto: string; onClick: () => void }[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {acciones.map((a) => (
        <button
          key={a.texto}
          onClick={a.onClick}
          className="rounded-full border border-border bg-card px-4 py-2 text-sm font-medium transition-colors hover:border-accent/50 hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {a.texto}
        </button>
      ))}
    </div>
  );
}

export function ConfirmCard({
  titulo,
  detalles,
  onConfirmar,
  onCancelar,
  pending = false,
  confirmLabel = "Confirmar reserva",
}: {
  titulo: string;
  detalles: string[];
  onConfirmar: () => void;
  onCancelar?: () => void;
  /** Bloquea ambos botones mientras la confirmación está en vuelo. */
  pending?: boolean;
  confirmLabel?: string;
}) {
  return (
    <div className="rounded-xl border border-accent/40 bg-accent/8 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        Confirma antes de continuar
      </p>
      <p className="mt-2 text-sm font-semibold">{titulo}</p>
      <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
        {detalles.map((d) => (
          <li key={d}>{d}</li>
        ))}
      </ul>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          disabled={pending}
          onClick={onConfirmar}
          className="rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? "Enviando…" : confirmLabel}
        </button>
        <button
          disabled={pending}
          onClick={onCancelar}
          className="rounded-full border border-border bg-card px-5 py-2 text-sm font-semibold transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}

export function AlertCard({
  tone = "destructive",
  titulo,
  detalle,
  traceId,
  onRetry,
  retryLabel = "Reintentar",
}: {
  tone?: "destructive" | "warning";
  titulo: string;
  detalle: string;
  traceId?: string;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  const toneClass =
    tone === "destructive"
      ? "border-destructive/35 bg-destructive/8 text-destructive"
      : "border-warning/40 bg-warning/10 text-warning";
  return (
    <div className={cn("rounded-xl border p-4", toneClass)}>
      <div className="flex items-center gap-2">
        <AlertTriangle className="size-4" />
        <p className="text-sm font-semibold">{titulo}</p>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{detalle}</p>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <RefreshCw className="size-4" /> {retryLabel}
        </button>
      ) : null}
      {traceId ? (
        <p className="mono mt-3 text-xs text-muted-foreground">trace_id: {traceId}</p>
      ) : null}
    </div>
  );
}

const dias = [
  { fecha: "10", dia: "lun", libres: 0 },
  { fecha: "11", dia: "mar", libres: 3 },
  { fecha: "12", dia: "mié", libres: 6 },
  { fecha: "13", dia: "jue", libres: 2 },
  { fecha: "14", dia: "vie", libres: 5 },
  { fecha: "15", dia: "sáb", libres: 0 },
];

const horas = [
  { h: "08:30", libre: false },
  { h: "09:00", libre: true },
  { h: "09:30", libre: true },
  { h: "10:00", libre: true },
  { h: "10:30", libre: false },
  { h: "11:00", libre: true },
];

export function InlineDatePicker({
  dia,
  hora,
  onDia,
  onHora,
  onConfirmar,
}: {
  dia: string;
  hora: string;
  onDia: (d: string) => void;
  onHora: (h: string) => void;
  onConfirmar: () => void;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Elige el día
      </p>
      <ul className="mt-3 grid grid-cols-3 gap-2">
        {dias.map((d) => {
          const activo = dia === d.fecha;
          const libre = d.libres > 0;
          return (
            <li key={d.fecha}>
              <button
                disabled={!libre}
                onClick={() => onDia(d.fecha)}
                className={cn(
                  "w-full rounded-xl border px-2 py-2.5 text-center transition-colors",
                  activo && libre ? "border-accent bg-accent/12" : "border-border bg-background",
                  !libre && "cursor-not-allowed opacity-55",
                )}
              >
                <span className="block text-xs text-muted-foreground">{d.dia}</span>
                <span className="mono block text-base font-semibold">{d.fecha}</span>
              </button>
            </li>
          );
        })}
      </ul>

      <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Elige la hora
      </p>
      <ul className="mt-3 grid grid-cols-3 gap-2">
        {horas.map((s) => {
          const activo = hora === s.h && s.libre;
          return (
            <li key={s.h}>
              <button
                disabled={!s.libre}
                onClick={() => onHora(s.h)}
                className={cn(
                  "mono w-full rounded-full border px-2 py-2 text-sm transition-colors",
                  activo
                    ? "border-accent bg-accent/12 font-semibold"
                    : "border-border bg-background",
                  !s.libre && "cursor-not-allowed text-muted-foreground line-through opacity-60",
                )}
              >
                {s.h}
              </button>
            </li>
          );
        })}
      </ul>

      <button
        onClick={onConfirmar}
        className="mt-4 w-full rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        Agendar {dia} de agosto · {hora}
      </button>
    </div>
  );
}
