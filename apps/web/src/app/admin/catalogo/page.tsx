import type { Metadata } from "next";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";

export const metadata: Metadata = {
  title: "Catálogo de agentes y herramientas — Nexo AI",
  description: "Agentes y herramientas disponibles con versión y estado de salud.",
  openGraph: {
    title: "Catálogo de agentes y herramientas — Nexo AI",
    description: "Inventario operativo con badges de versión y salud.",
  },
};

type Item = {
  nombre: string;
  tipo: "Agente" | "Herramienta";
  descripcion: string;
  version: string;
  salud: "Activo" | "Degradado" | "Caído";
  tone: Tone;
  usos: string;
};

const items: Item[] = [
  {
    nombre: "agente_vehiculos",
    tipo: "Agente",
    descripcion: "Traspasos, placas y revisión técnica.",
    version: "v4.2.0",
    salud: "Activo",
    tone: "success",
    usos: "842 runs / 7 d",
  },
  {
    nombre: "agente_empresas",
    tipo: "Agente",
    descripcion: "Constitución y registro de empresas.",
    version: "v3.8.1",
    salud: "Activo",
    tone: "success",
    usos: "517 runs / 7 d",
  },
  {
    nombre: "agente_registro_civil",
    tipo: "Agente",
    descripcion: "Certificados de nacimiento y matrimonio.",
    version: "v2.9.4",
    salud: "Degradado",
    tone: "warning",
    usos: "431 runs / 7 d",
  },
  {
    nombre: "agente_salud",
    tipo: "Agente",
    descripcion: "Citas médicas y afiliaciones.",
    version: "v1.6.0",
    salud: "Activo",
    tone: "success",
    usos: "298 runs / 7 d",
  },
  {
    nombre: "agente_ganaderia",
    tipo: "Agente",
    descripcion: "Registro de hato y guías de movilización.",
    version: "v1.2.3",
    salud: "Caído",
    tone: "destructive",
    usos: "188 runs / 7 d",
  },
  {
    nombre: "consultar_requisitos",
    tipo: "Herramienta",
    descripcion: "Lee el catálogo institucional de requisitos.",
    version: "v5.0.2",
    salud: "Activo",
    tone: "success",
    usos: "2.1 k llamadas",
  },
  {
    nombre: "validar_documento",
    tipo: "Herramienta",
    descripcion: "OCR y validación de documentos cargados.",
    version: "v2.4.7",
    salud: "Degradado",
    tone: "warning",
    usos: "1.4 k llamadas",
  },
  {
    nombre: "reservar_cita",
    tipo: "Herramienta",
    descripcion: "Escribe en la agenda institucional.",
    version: "v3.1.0",
    salud: "Activo",
    tone: "success",
    usos: "612 llamadas",
  },
];

export default function Page() {
  return (
    <AdminShell
      title="Catálogo"
      subtitle="Agentes y herramientas registrados en la plataforma"
      actions={<StatusBadge tone="warning">2 degradados · 1 caído</StatusBadge>}
    >
      <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((i) => (
          <li key={i.nombre} className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
              <div className="min-w-0">
                <p className="mono truncate text-sm font-semibold">{i.nombre}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{i.tipo}</p>
              </div>
              <StatusBadge tone={i.tone}>{i.salud}</StatusBadge>
            </div>
            <p className="mt-3 text-sm text-muted-foreground">{i.descripcion}</p>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="mono rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground">
                {i.version}
              </span>
              <span className="text-xs text-muted-foreground">{i.usos}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="rounded-full border border-border px-4 py-1.5 text-xs font-medium transition-colors hover:bg-secondary">
                Ver contrato
              </button>
              <button className="rounded-full border border-border px-4 py-1.5 text-xs font-medium transition-colors hover:bg-secondary">
                Historial de versiones
              </button>
            </div>
          </li>
        ))}
      </ul>
    </AdminShell>
  );
}
