import { Rail, RailItem } from "@/components/nexo/rail";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";

export function ChatTimeline({
  eventos,
}: {
  eventos: { estado: string; detalle: string; tone: Tone; done?: boolean; active?: boolean }[];
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Línea de tiempo
      </p>
      <Rail>
        {eventos.map((e) => (
          <RailItem key={e.estado} done={e.done} active={e.active}>
            <p className="text-sm font-semibold">{e.estado}</p>
            <p className="mt-0.5 text-sm text-muted-foreground">{e.detalle}</p>
            <StatusBadge tone={e.tone} className="mt-2">
              {e.done ? "Completado" : e.active ? "En curso" : "Pendiente"}
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
