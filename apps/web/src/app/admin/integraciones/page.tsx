import type { Metadata } from "next";
import { AlertTriangle, Brain, Database, MessageCircle, PhoneCall } from "lucide-react";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";

export const metadata: Metadata = {
  title: "Integraciones — Nexo AI",
  description: "Estado de salud, última ejecución y errores recientes por proveedor.",
  openGraph: {
    title: "Integraciones — Nexo AI",
    description: "Proveedores de mensajería, voz, modelos y almacenamiento.",
  },
};

const proveedores = [
  {
    nombre: "WhatsApp Business",
    icono: MessageCircle,
    descripcion: "Canal principal de atención ciudadana.",
    salud: "Operativo",
    tone: "success" as Tone,
    ultima: "Hace 12 s",
    latencia: "180 ms",
    errores: [] as string[],
  },
  {
    nombre: "Telefonía y voz",
    icono: PhoneCall,
    descripcion: "Llamadas entrantes y transcripción en vivo.",
    salud: "Degradado",
    tone: "warning" as Tone,
    ultima: "Hace 1 min",
    latencia: "940 ms",
    errores: ["08:55 · timeout al abrir el stream de audio (3 casos)"],
  },
  {
    nombre: "Modelos de lenguaje",
    icono: Brain,
    descripcion: "Comprensión, redacción y clasificación.",
    salud: "Operativo",
    tone: "success" as Tone,
    ultima: "Hace 4 s",
    latencia: "620 ms",
    errores: [],
  },
  {
    nombre: "Almacenamiento documental",
    icono: Database,
    descripcion: "Documentos ciudadanos y evidencias del trámite.",
    salud: "Caído",
    tone: "destructive" as Tone,
    ultima: "Hace 22 min",
    latencia: "—",
    errores: [
      "09:18 · 503 al subir archivo (12 casos)",
      "09:05 · error de escritura en bucket tramites-2026",
    ],
  },
];

export default function Page() {
  return (
    <AdminShell
      title="Integraciones"
      subtitle="Proveedores conectados a la plataforma"
      actions={<StatusBadge tone="destructive">1 proveedor caído</StatusBadge>}
    >
      <ul className="grid gap-3 md:grid-cols-2">
        {proveedores.map((p) => (
          <li key={p.nombre} className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-secondary text-secondary-foreground">
                  <p.icono className="size-5" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-base font-semibold">{p.nombre}</p>
                  <p className="truncate text-xs text-muted-foreground">{p.descripcion}</p>
                </div>
              </div>
              <StatusBadge tone={p.tone}>{p.salud}</StatusBadge>
            </div>

            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">Última ejecución</dt>
                <dd className="mono mt-0.5">{p.ultima}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Latencia media</dt>
                <dd className="mono mt-0.5">{p.latencia}</dd>
              </div>
            </dl>

            <div className="mt-4 rounded-xl border border-border bg-background p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Errores recientes
              </p>
              {p.errores.length === 0 ? (
                <p className="mt-2 text-sm text-muted-foreground">
                  Sin errores en las últimas 24 horas.
                </p>
              ) : (
                <ul className="mt-2 space-y-1.5">
                  {p.errores.map((e) => (
                    <li key={e} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-destructive" />
                      <span className="mono text-xs">{e}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <button className="rounded-full border border-border px-4 py-1.5 text-xs font-medium transition-colors hover:bg-secondary">
                Ver registros
              </button>
              <button className="rounded-full border border-border px-4 py-1.5 text-xs font-medium transition-colors hover:bg-secondary">
                Probar conexión
              </button>
            </div>
          </li>
        ))}
      </ul>
    </AdminShell>
  );
}
