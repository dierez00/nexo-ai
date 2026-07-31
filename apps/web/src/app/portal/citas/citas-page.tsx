"use client";

import { useState } from "react";
import { CalendarCheck, Clock, MapPin } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { cn } from "@/lib/utils";

const dias = [
  { fecha: "10", dia: "lun", mes: "ago", libres: 0 },
  { fecha: "11", dia: "mar", mes: "ago", libres: 3 },
  { fecha: "12", dia: "mié", mes: "ago", libres: 6 },
  { fecha: "13", dia: "jue", mes: "ago", libres: 2 },
  { fecha: "14", dia: "vie", mes: "ago", libres: 5 },
  { fecha: "15", dia: "sáb", mes: "ago", libres: 0 },
];

const horas = [
  { h: "08:30", libre: false },
  { h: "09:00", libre: true },
  { h: "09:30", libre: true },
  { h: "10:00", libre: true },
  { h: "10:30", libre: false },
  { h: "11:00", libre: true },
  { h: "14:00", libre: true },
  { h: "14:30", libre: false },
  { h: "15:00", libre: true },
];

export function CitasPage() {
  const [dia, setDia] = useState("12");
  const [hora, setHora] = useState("10:00");

  return (
    <PortalShell
      title="Reservar cita presencial"
      subtitle="Traspaso de vehículo · Oficina Central de Tránsito"
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            1. Elige el día
          </h2>
          <ul className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-6">
            {dias.map((d) => {
              const activo = dia === d.fecha;
              const libre = d.libres > 0;
              return (
                <li key={d.fecha}>
                  <button
                    disabled={!libre}
                    onClick={() => setDia(d.fecha)}
                    className={cn(
                      "w-full rounded-xl border px-2 py-3 text-center transition-colors",
                      activo && libre
                        ? "border-accent bg-accent/12 text-foreground"
                        : "border-border bg-background",
                      !libre && "cursor-not-allowed opacity-55",
                    )}
                  >
                    <span className="block text-xs text-muted-foreground">{d.dia}</span>
                    <span className="mono block text-lg font-semibold">{d.fecha}</span>
                    <span className="block text-[10px] text-muted-foreground">
                      {libre ? `${d.libres} cupos` : "sin cupos"}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          <h2 className="mt-7 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            2. Elige la hora
          </h2>
          <ul className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-5">
            {horas.map((s) => {
              const activo = hora === s.h && s.libre;
              return (
                <li key={s.h}>
                  <button
                    disabled={!s.libre}
                    onClick={() => setHora(s.h)}
                    className={cn(
                      "mono w-full rounded-full border px-2 py-2 text-sm transition-colors",
                      activo
                        ? "border-accent bg-accent/12 font-semibold"
                        : "border-border bg-background",
                      !s.libre &&
                        "cursor-not-allowed text-muted-foreground line-through opacity-60",
                    )}
                  >
                    {s.h}
                  </button>
                </li>
              );
            })}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            Los horarios tachados ya están ocupados. Cada cita dura 30 minutos.
          </p>
        </section>

        <section className="h-fit rounded-2xl border border-accent/30 bg-accent/8 p-5 shadow-soft lg:sticky lg:top-24">
          <StatusBadge tone="accent">Resumen de tu cita</StatusBadge>
          <p className="mt-4 text-xl font-bold">
            {dia} de agosto · {hora}
          </p>
          <ul className="mt-4 space-y-2.5 text-sm">
            <li className="flex items-start gap-2.5">
              <CalendarCheck className="mt-0.5 size-4 shrink-0 text-accent" />
              <span>
                Traspaso de vehículo · placa <span className="mono">ABC-4821</span>
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <MapPin className="mt-0.5 size-4 shrink-0 text-accent" />
              <span>Oficina Central de Tránsito, Av. Libertad 1204, ventanilla 6</span>
            </li>
            <li className="flex items-start gap-2.5">
              <Clock className="mt-0.5 size-4 shrink-0 text-accent" />
              <span>Duración estimada: 30 minutos. Llega 10 minutos antes.</span>
            </li>
          </ul>
          <div className="mt-5 rounded-xl border border-border bg-card p-3 text-sm">
            <p className="font-medium">Lleva contigo</p>
            <p className="mt-1 text-muted-foreground">
              Cédula original, título de propiedad y comprobante de pago del arancel.
            </p>
          </div>
          <button className="mt-5 w-full rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90">
            Confirmar cita
          </button>
          <button className="mt-2 w-full rounded-full border border-border bg-card px-6 py-3 text-sm font-semibold transition-colors hover:bg-secondary">
            Elegir otro horario
          </button>
        </section>
      </div>
    </PortalShell>
  );
}
