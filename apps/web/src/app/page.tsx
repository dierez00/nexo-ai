import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, MessageSquare, Mic, ShieldCheck } from "lucide-react";
import { ThemeToggle } from "@/components/nexo/theme-toggle";
import { StatusBadge } from "@/components/nexo/status-badge";

export const metadata: Metadata = {
  title: "Nexo AI — Trámites institucionales por WhatsApp, voz o web",
  description:
    "Resuelve trámites de vehículos, empresas, registro civil, salud y ganadería con acompañamiento guiado y trazabilidad completa.",
  openGraph: {
    title: "Nexo AI — Trámites institucionales sin filas",
    description: "Portal ciudadano y consola interna con trazabilidad de cada paso del trámite.",
  },
};

const canales = [
  {
    icon: MessageSquare,
    titulo: "WhatsApp",
    texto: "Escribe como a una persona y recibe pasos claros.",
  },
  {
    icon: Mic,
    titulo: "Llamada de voz",
    texto: "Habla con el agente y confirma tus datos en voz alta.",
  },
  {
    icon: ShieldCheck,
    titulo: "Portal web",
    texto: "Sube documentos y sigue tu folio en tiempo real.",
  },
];

export default function Page() {
  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto grid max-w-5xl grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-4 sm:px-6">
        <span className="wordmark truncate">Nexo AI</span>
        <ThemeToggle />
      </header>

      <main className="mx-auto max-w-5xl px-4 pb-20 sm:px-6">
        <section className="pt-10 sm:pt-16">
          <StatusBadge tone="accent">Mockup de interfaz · datos de ejemplo</StatusBadge>
          <h1 className="mt-5 text-3xl font-extrabold leading-tight tracking-tight sm:text-5xl">
            Tus trámites institucionales, acompañados paso a paso.
          </h1>
          <p className="mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
            Vehículos, apertura de empresas, registro civil, salud y ganadería. Un mismo expediente,
            sin importar si escribes por WhatsApp, llamas o entras al portal.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link
              href="/portal"
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              Entrar al portal ciudadano <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/admin"
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-6 py-3 text-sm font-semibold transition-colors hover:bg-secondary"
            >
              Abrir consola interna
            </Link>
          </div>
        </section>

        <section className="mt-14 grid gap-4 sm:grid-cols-3">
          {canales.map((c) => (
            <article
              key={c.titulo}
              className="rounded-2xl border border-border bg-card p-5 shadow-soft"
            >
              <c.icon className="size-5 text-accent" />
              <h2 className="mt-3 text-base font-semibold">{c.titulo}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{c.texto}</p>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
