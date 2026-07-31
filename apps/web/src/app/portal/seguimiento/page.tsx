import type { Metadata } from "next";
import Link from "next/link";
import { Copy, ExternalLink, LifeBuoy, Upload } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { Rail, RailItem } from "@/components/nexo/rail";

export const metadata: Metadata = {
  title: "Seguimiento del trámite — Nexo AI",
  description:
    "Sigue tu folio paso a paso: qué pasó, quién lo informó y cuál es la siguiente acción.",
  openGraph: {
    title: "Seguimiento del trámite — Nexo AI",
    description: "Línea de tiempo con trazabilidad de estado, fuente y acción.",
  },
};

const eventos = [
  {
    fecha: "24 jul · 10:12",
    estado: "Solicitud recibida",
    tone: "success" as const,
    detalle: "Abriste el trámite desde WhatsApp y verificamos tu identidad.",
    fuente: "Registro Único Automotor",
    done: true,
  },
  {
    fecha: "25 jul · 08:40",
    estado: "Documentos recibidos",
    tone: "success" as const,
    detalle: "Cédula y título de propiedad validados automáticamente.",
    fuente: "Validador documental Nexo",
    done: true,
  },
  {
    fecha: "29 jul · 16:05",
    estado: "En revisión documental",
    tone: "warning" as const,
    detalle: "Falta el certificado de no adeudo de multas para continuar.",
    fuente: "Oficina Central de Tránsito",
    done: false,
    activo: true,
  },
  {
    fecha: "Pendiente",
    estado: "Cita presencial",
    tone: "neutral" as const,
    detalle: "Se habilita cuando se completen los requisitos.",
    fuente: "Agenda institucional",
    done: false,
  },
  {
    fecha: "Pendiente",
    estado: "Entrega del nuevo título",
    tone: "neutral" as const,
    detalle: "Retiro en ventanilla o envío a domicilio.",
    fuente: "Oficina Central de Tránsito",
    done: false,
  },
];

export default function Page() {
  return (
    <PortalShell title="Seguimiento" subtitle="Traspaso de vehículo · placa ABC-4821">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div className="space-y-4">
          <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
              <div className="min-w-0">
                <p className="text-sm text-muted-foreground">Folio del trámite</p>
                <p className="mono mt-1 truncate text-xl font-semibold">NX-2026-004821</p>
              </div>
              <button className="inline-flex shrink-0 items-center gap-2 rounded-full border border-border px-3 py-1.5 text-xs font-medium">
                <Copy className="size-3.5" /> Copiar folio
              </button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <StatusBadge tone="warning">En revisión documental</StatusBadge>
              <StatusBadge tone="info">Canal: WhatsApp</StatusBadge>
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Línea de tiempo
            </h2>
            <Rail>
              {eventos.map((e) => (
                <RailItem key={e.estado} done={e.done} active={e.activo}>
                  <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                    <p className="min-w-0 text-sm font-semibold">{e.estado}</p>
                    <span className="mono shrink-0 text-xs text-muted-foreground">{e.fecha}</span>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{e.detalle}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <StatusBadge tone={e.tone}>
                      {e.done ? "Completado" : e.activo ? "En curso" : "Pendiente"}
                    </StatusBadge>
                    <a
                      href="#"
                      className="inline-flex items-center gap-1.5 text-xs text-info underline underline-offset-4"
                    >
                      Fuente: {e.fuente} <ExternalLink className="size-3" />
                    </a>
                  </div>
                </RailItem>
              ))}
            </Rail>
          </section>
        </div>

        <div className="space-y-4 lg:sticky lg:top-24 lg:h-fit">
          <section className="rounded-2xl border border-accent/35 bg-accent/8 p-5 shadow-soft">
            <StatusBadge tone="accent">Próxima acción</StatusBadge>
            <h2 className="mt-3 text-lg font-bold">Sube el certificado de no adeudo</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Es el único documento que falta. Al recibirlo, habilitamos tu cita en menos de 24
              horas.
            </p>
            <button className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground">
              <Upload className="size-4" /> Subir documento
            </button>
            <Link
              href="/portal/citas"
              className="mt-2 inline-flex w-full items-center justify-center rounded-full border border-border bg-card px-6 py-3 text-sm font-semibold"
            >
              Ver cupos de cita
            </Link>
          </section>

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
