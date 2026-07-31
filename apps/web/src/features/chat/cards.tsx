import {
  CalendarCheck,
  CheckCircle2,
  Circle,
  Clock,
  Download,
  ExternalLink,
  FileText,
  MapPin,
  Share2,
} from "lucide-react";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { cn } from "@/lib/utils";

export function InfoCard({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {eyebrow}
      </p>
      {title ? <p className="mt-1 text-sm font-medium">{title}</p> : null}
      {children}
    </div>
  );
}

export function SourceCard({
  titulo,
  actualizado,
  doc,
}: {
  titulo: string;
  actualizado: string;
  doc: string;
}) {
  return (
    <div className="rail rounded-xl border border-border bg-card p-4">
      <span aria-hidden className="rail-node bg-accent" />
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        Fuente oficial citada
      </p>
      <p className="mt-1 text-sm font-medium">{titulo}</p>
      <a
        href="#"
        className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-info underline underline-offset-4"
      >
        Ver documento en el portal institucional <ExternalLink className="size-3.5" />
      </a>
      <p className="mono mt-2 text-xs text-muted-foreground">
        Actualizado {actualizado} · {doc}
      </p>
    </div>
  );
}

export function DocumentsCard({
  titulo = "Requisitos",
  items,
}: {
  titulo?: string;
  items: { texto: string; ok: boolean }[];
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {titulo}
      </p>
      <ul className="mt-3 space-y-2">
        {items.map((i) => (
          <li key={i.texto} className="flex items-start gap-2.5 text-sm">
            {i.ok ? (
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
            ) : (
              <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
            )}
            <span className={cn(i.ok ? "text-foreground" : "text-muted-foreground")}>
              {i.texto} {i.ok ? "· entregado" : "· pendiente"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function UploadedDocsCard({
  items,
}: {
  items: { nombre: string; peso: string; estado: string; tone: Tone }[];
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Documentos subidos
      </p>
      <ul className="mt-3 space-y-2">
        {items.map((d) => (
          <li
            key={d.nombre}
            className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-border px-3 py-2.5"
          >
            <div className="flex min-w-0 items-center gap-2.5">
              <FileText className="size-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="mono truncate text-sm">{d.nombre}</p>
                <p className="text-xs text-muted-foreground">{d.peso}</p>
              </div>
            </div>
            <StatusBadge tone={d.tone}>{d.estado}</StatusBadge>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AppointmentCard({
  fecha,
  tramite,
  lugar,
  duracion,
}: {
  fecha: string;
  tramite: string;
  lugar: string;
  duracion: string;
}) {
  return (
    <div className="rounded-xl border border-accent/40 bg-accent/8 p-4">
      <StatusBadge tone="accent">Resumen de tu cita</StatusBadge>
      <p className="mt-3 text-lg font-bold">{fecha}</p>
      <ul className="mt-3 space-y-2 text-sm">
        <li className="flex items-start gap-2.5">
          <CalendarCheck className="mt-0.5 size-4 shrink-0 text-accent" />
          <span>{tramite}</span>
        </li>
        <li className="flex items-start gap-2.5">
          <MapPin className="mt-0.5 size-4 shrink-0 text-accent" />
          <span>{lugar}</span>
        </li>
        <li className="flex items-start gap-2.5">
          <Clock className="mt-0.5 size-4 shrink-0 text-accent" />
          <span>{duracion}</span>
        </li>
      </ul>
    </div>
  );
}

export function ReceiptCard({
  folio,
  tramite,
  fecha,
}: {
  folio: string;
  tramite: string;
  fecha: string;
}) {
  return (
    <div className="rounded-xl border border-success/35 bg-success/8 p-4">
      <StatusBadge tone="success">Trámite completado</StatusBadge>
      <p className="mt-3 text-sm font-semibold">{tramite}</p>
      <p className="mono mt-1 text-xs text-muted-foreground">
        Folio {folio} · {fecha}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90">
          <Download className="size-4" /> Descargar comprobante
        </button>
        <button className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm font-semibold transition-colors hover:bg-secondary">
          <Share2 className="size-4" /> Compartir
        </button>
      </div>
    </div>
  );
}

export function CostCard({
  items,
  total,
}: {
  items: { concepto: string; monto: string }[];
  total: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Costos estimados
      </p>
      <ul className="mt-3 space-y-2 text-sm">
        {items.map((c) => (
          <li key={c.concepto} className="flex items-baseline justify-between gap-3">
            <span className="min-w-0 text-muted-foreground">{c.concepto}</span>
            <span className="mono shrink-0 font-medium">{c.monto}</span>
          </li>
        ))}
      </ul>
      <div className="mt-3 flex items-baseline justify-between border-t border-border pt-3">
        <span className="text-sm font-semibold">Total estimado</span>
        <span className="mono text-base font-semibold">{total}</span>
      </div>
    </div>
  );
}
