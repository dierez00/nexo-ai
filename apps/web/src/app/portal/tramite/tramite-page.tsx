"use client";

import Link from "next/link";
import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  ExternalLink,
  FileText,
  RefreshCw,
  Upload,
} from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { Rail, RailItem } from "@/components/nexo/rail";
import { cn } from "@/lib/utils";

type Estado = "completo" | "vacio" | "cargando" | "error" | "parcial";
const estados: { id: Estado; label: string }[] = [
  { id: "completo", label: "Completo" },
  { id: "vacio", label: "Vacío" },
  { id: "cargando", label: "Cargando" },
  { id: "error", label: "Error" },
  { id: "parcial", label: "Datos parciales" },
];

const requisitos = [
  { texto: "Cédula de identidad vigente", ok: true },
  { texto: "Título de propiedad del vehículo", ok: true },
  { texto: "Certificado de no adeudo de multas", ok: false },
  { texto: "Comprobante de pago del arancel", ok: false },
];

const documentos = [
  { nombre: "cedula_andrea.pdf", peso: "480 KB", estado: "Validado", tone: "success" as const },
  { nombre: "titulo_propiedad.pdf", peso: "1,2 MB", estado: "Validado", tone: "success" as const },
  { nombre: "no_adeudo.pdf", peso: "—", estado: "Falta subir", tone: "warning" as const },
];

const costos = [
  { concepto: "Arancel de traspaso", monto: "350,00 Bs" },
  { concepto: "Formulario de notificación", monto: "45,00 Bs" },
  { concepto: "Certificación de no adeudo", monto: "60,00 Bs" },
];

function Bloque({
  titulo,
  children,
  extra,
}: {
  titulo: string;
  children: React.ReactNode;
  extra?: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
      <div className="mb-4 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
        <h2 className="truncate text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {titulo}
        </h2>
        {extra}
      </div>
      {children}
    </section>
  );
}

export function TramitePage() {
  const [estado, setEstado] = useState<Estado>("completo");

  return (
    <PortalShell
      title="Traspaso de vehículo"
      subtitle="Folio NX-2026-004821 · iniciado el 24 de julio de 2026"
    >
      <div className="mb-5 flex flex-wrap gap-2">
        {estados.map((e) => (
          <button
            key={e.id}
            onClick={() => setEstado(e.id)}
            className={cn(
              "rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
              estado === e.id
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-card text-muted-foreground hover:text-foreground",
            )}
          >
            {e.label}
          </button>
        ))}
      </div>

      {estado === "vacio" ? (
        <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center shadow-soft">
          <FileText className="mx-auto size-6 text-muted-foreground" />
          <p className="mt-3 text-lg font-semibold">Todavía no tienes trámites abiertos</p>
          <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
            Cuando inicies un trámite verás aquí su estado, requisitos y costos. Puedes empezar
            preguntando al asistente.
          </p>
          <Link
            href="/portal/chat"
            className="mt-5 inline-flex rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground"
          >
            Iniciar un trámite
          </Link>
        </div>
      ) : null}

      {estado === "cargando" ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          {[0, 1].map((c) => (
            <div key={c} className="space-y-4">
              {[0, 1].map((i) => (
                <div key={i} className="space-y-3 rounded-2xl border border-border bg-card p-5">
                  <div className="h-3 w-32 animate-pulse rounded-full bg-muted" />
                  <div className="h-3 w-full animate-pulse rounded-full bg-muted" />
                  <div className="h-3 w-4/5 animate-pulse rounded-full bg-muted" />
                  <div className="h-3 w-2/3 animate-pulse rounded-full bg-muted" />
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : null}

      {estado === "error" ? (
        <div className="rounded-2xl border border-destructive/35 bg-destructive/8 p-6 shadow-soft">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="size-5" />
            <h2 className="text-base font-semibold">No pudimos cargar tu trámite</h2>
          </div>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">
            El registro institucional de vehículos está fuera de servicio. Tus documentos ya
            cargados están a salvo y ningún plazo se ve afectado.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <button className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground">
              <RefreshCw className="size-4" /> Volver a intentar
            </button>
            <Link
              href="/portal/chat"
              className="rounded-full border border-border bg-card px-5 py-2.5 text-sm font-semibold"
            >
              Avisar al asistente
            </Link>
          </div>
          <p className="mono mt-4 text-xs text-muted-foreground">
            folio NX-2026-004821 · trc_71fe20aa03
          </p>
        </div>
      ) : null}

      {estado === "parcial" ? (
        <div className="grid gap-4">
          <div className="rounded-2xl border border-warning/40 bg-warning/10 p-5 shadow-soft">
            <StatusBadge tone="warning">Mostrando datos parciales</StatusBadge>
            <p className="mt-3 text-sm text-muted-foreground">
              Pudimos leer tu expediente, pero el sistema de multas no respondió. Esto es lo que
              sabemos hoy.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Bloque titulo="Confirmado">
              <ul className="space-y-2 text-sm">
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" /> Titular
                  verificado: Andrea Peñaranda
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" /> Placa{" "}
                  <span className="mono">ABC-4821</span> registrada
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" /> 2 de 4 documentos
                  validados
                </li>
              </ul>
            </Bloque>
            <Bloque titulo="Pendiente de confirmar">
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex gap-2">
                  <Circle className="mt-0.5 size-4 shrink-0" /> Deuda por multas (fuente no
                  disponible)
                </li>
                <li className="flex gap-2">
                  <Circle className="mt-0.5 size-4 shrink-0" /> Costo total definitivo
                </li>
                <li className="flex gap-2">
                  <Circle className="mt-0.5 size-4 shrink-0" /> Fecha de cita en oficina
                </li>
              </ul>
              <button className="mt-4 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground">
                Reintentar consulta de multas
              </button>
            </Bloque>
          </div>
        </div>
      ) : null}

      {estado === "completo" ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          <div className="space-y-4">
            <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-muted-foreground">Estado actual</p>
                  <p className="mt-1 text-xl font-bold">En revisión documental</p>
                </div>
                <StatusBadge tone="warning">Paso 3 de 5</StatusBadge>
              </div>
              <Rail className="mt-5">
                <RailItem done>
                  <p className="text-sm font-semibold">Estado</p>
                  <p className="text-sm text-muted-foreground">
                    Expediente abierto y titular verificado.
                  </p>
                </RailItem>
                <RailItem done>
                  <p className="text-sm font-semibold">Fuente</p>
                  <p className="text-sm text-muted-foreground">
                    Registro Único Automotor · consulta del 29/07/2026.
                  </p>
                </RailItem>
                <RailItem active>
                  <p className="text-sm font-semibold">Siguiente acción</p>
                  <p className="text-sm text-muted-foreground">
                    Sube el certificado de no adeudo para pasar a agenda.
                  </p>
                  <button className="mt-3 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground">
                    <Upload className="size-4" /> Subir documento
                  </button>
                </RailItem>
              </Rail>
            </section>

            <Bloque
              titulo="Requisitos"
              extra={<StatusBadge tone="info">2 de 4 listos</StatusBadge>}
            >
              <ul className="space-y-2.5">
                {requisitos.map((r) => (
                  <li key={r.texto} className="flex items-start gap-2.5 text-sm">
                    {r.ok ? (
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                    ) : (
                      <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    )}
                    <span className={r.ok ? "" : "text-muted-foreground"}>
                      {r.texto} · {r.ok ? "entregado" : "pendiente"}
                    </span>
                  </li>
                ))}
              </ul>
            </Bloque>

            <Bloque titulo="Documentos subidos">
              <ul className="space-y-2">
                {documentos.map((d) => (
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
            </Bloque>
          </div>

          <div className="space-y-4">
            <Bloque titulo="Costos estimados">
              <ul className="space-y-2 text-sm">
                {costos.map((c) => (
                  <li key={c.concepto} className="flex items-baseline justify-between gap-3">
                    <span className="min-w-0 text-muted-foreground">{c.concepto}</span>
                    <span className="mono shrink-0 font-medium">{c.monto}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-3 flex items-baseline justify-between border-t border-border pt-3">
                <span className="text-sm font-semibold">Total estimado</span>
                <span className="mono text-base font-semibold">455,00 Bs</span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Referencial. El monto final se confirma en ventanilla.
              </p>
            </Bloque>

            <Bloque titulo="Pasos siguientes">
              <ol className="space-y-3 text-sm">
                <li className="flex gap-3">
                  <span className="mono shrink-0 text-accent">01</span>
                  <span>Subir el certificado de no adeudo de multas.</span>
                </li>
                <li className="flex gap-3">
                  <span className="mono shrink-0 text-accent">02</span>
                  <span>Pagar el arancel y adjuntar el comprobante.</span>
                </li>
                <li className="flex gap-3">
                  <span className="mono shrink-0 text-accent">03</span>
                  <span>Reservar cita presencial para la firma.</span>
                </li>
              </ol>
              <Link
                href="/portal/citas"
                className="mt-4 inline-flex rounded-full border border-border bg-card px-5 py-2 text-sm font-semibold transition-colors hover:bg-secondary"
              >
                Reservar cita
              </Link>
            </Bloque>

            <Bloque titulo="Fuentes oficiales citadas">
              <ul className="space-y-3">
                {[
                  { t: "Reglamento de Tránsito — Art. 47", d: "Actualizado 12/06/2026" },
                  { t: "Tarifario vigente de aranceles 2026", d: "Actualizado 02/01/2026" },
                ].map((f) => (
                  <li key={f.t} className="rail">
                    <span aria-hidden className="rail-node bg-accent" />
                    <p className="text-sm font-medium">{f.t}</p>
                    <a
                      href="#"
                      className="mt-1 inline-flex items-center gap-1.5 text-sm text-info underline underline-offset-4"
                    >
                      Abrir fuente <ExternalLink className="size-3.5" />
                    </a>
                    <p className="text-xs text-muted-foreground">{f.d}</p>
                  </li>
                ))}
              </ul>
            </Bloque>
          </div>
        </div>
      ) : null}
    </PortalShell>
  );
}
