import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  MessageSquare,
  Mic,
  Route as RouteIcon,
  Sparkle,
} from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";

export const metadata: Metadata = {
  title: "Portal ciudadano — Nexo AI",
  description:
    "Consulta tus solicitudes recientes, retoma un trámite sugerido y habla con el agente.",
  openGraph: {
    title: "Portal ciudadano — Nexo AI",
    description: "Tus trámites, su estado y la siguiente acción, en un solo lugar.",
  },
};

const atajos = [
  {
    to: "/portal/chat",
    icon: MessageSquare,
    titulo: "Iniciar un trámite",
    texto: "Cuéntale al asistente qué necesitas resolver.",
  },
  {
    to: "/portal/chat",
    icon: RouteIcon,
    titulo: "Ver mis trámites",
    texto: "Consulta el estado y la siguiente acción en el chat.",
  },
  {
    to: "/portal/chat",
    icon: CalendarDays,
    titulo: "Agendar una cita",
    texto: "Elige fecha y hora sin salir de la conversación.",
  },
  {
    to: "/agente-voz",
    icon: Mic,
    titulo: "Hablar con el agente de voz",
    texto: "Resuelve por llamada, sin escribir.",
  },
] as const;

export default function Page() {
  return (
    <PortalShell
      title="Portal ciudadano"
      subtitle="Todo tu trámite ocurre en una sola conversación."
    >
      <section className="rounded-2xl border border-accent/30 bg-accent/8 p-5 shadow-soft">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
          <div className="min-w-0">
            <StatusBadge tone="accent">Trámite sugerido para ti</StatusBadge>
            <h2 className="mt-3 text-lg font-bold">Renueva tu licencia de conducir</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Tu licencia vence el 18 de agosto. Puedes agendar la cita en el chat en 3 pasos.
            </p>
          </div>
          <Sparkle className="hidden size-5 shrink-0 text-accent sm:block" />
        </div>
        <div className="mt-4">
          <Link
            href="/portal/chat"
            className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
          >
            Empezar en el chat <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>

      <section className="mt-10">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Atajos
        </h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          {atajos.map((a) => (
            <li key={a.titulo}>
              <Link
                href={a.to}
                className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5 shadow-soft transition-colors hover:bg-secondary"
              >
                <span className="grid size-11 shrink-0 place-items-center rounded-full bg-secondary text-secondary-foreground">
                  <a.icon className="size-5" />
                </span>
                <span className="min-w-0">
                  <span className="block text-base font-semibold">{a.titulo}</span>
                  <span className="block text-sm text-muted-foreground">{a.texto}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </PortalShell>
  );
}
