"use client";

/**
 * Esta página asume que quien enlaza aquí ya sabe la oficina y el módulo
 * (típicamente un botón de una superficie A2UI del chat): no existe un
 * directorio de sucursales en el backend, así que `branch_id`/`module_code`/
 * `service_name` llegan por query string. Sin ellos no hay forma segura de
 * adivinar una sucursal real, así que la página lo dice en vez de inventar un
 * valor por defecto que podría apuntar a datos de otra oficina.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CalendarCheck, Clock, LinkIcon, MapPin, RefreshCw, SearchX } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { cn } from "@/lib/utils";
import {
  ApiError,
  createAppointmentHold,
  getAppointmentAvailability,
  getOrCreateIdempotencyKey,
  type AppointmentHold,
  type AppointmentSlot,
} from "@/lib/api/client";

type LoadState = "loading" | "loaded" | "error";

function isoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function nextDays(count: number): Date[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Array.from({ length: count }, (_, index) => {
    const day = new Date(today);
    day.setDate(day.getDate() + index);
    return day;
  });
}

function formatHour(iso: string) {
  return new Date(iso).toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit" });
}

export function CitasPage() {
  const searchParams = useSearchParams();
  const branchIdParam = searchParams.get("branch_id");
  const moduleCode = searchParams.get("module_code");
  const serviceName = searchParams.get("service_name");
  const branchId = branchIdParam ? Number(branchIdParam) : null;
  const missingLinkInfo = !branchId || !moduleCode || !serviceName;

  return missingLinkInfo ? (
    <PortalShell title="Reservar cita presencial">
      <div className="mx-auto max-w-md rounded-2xl border border-dashed border-border bg-card p-8 text-center shadow-soft">
        <LinkIcon className="mx-auto size-6 text-muted-foreground" />
        <p className="mt-3 text-lg font-semibold">Este enlace está incompleto</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
          Falta la sucursal, el módulo o el servicio a agendar. Pide la cita desde el chat: el
          asistente arma el enlace correcto cuando corresponde.
        </p>
        <Link
          href="/portal/chat"
          className="mt-5 inline-flex rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground"
        >
          Ir al chat
        </Link>
      </div>
    </PortalShell>
  ) : (
    <CitasPageContent branchId={branchId} moduleCode={moduleCode} serviceName={serviceName} />
  );
}

function CitasPageContent({
  branchId,
  moduleCode,
  serviceName,
}: {
  branchId: number;
  moduleCode: string;
  serviceName: string;
}) {

  const days = useMemo(() => nextDays(6), []);
  const [selectedDay, setSelectedDay] = useState(() => isoDate(days[0]));
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<AppointmentSlot | null>(null);
  const [hold, setHold] = useState<AppointmentHold | null>(null);
  const [confirming, setConfirming] = useState(false);

  const loadAvailability = useCallback(async () => {
    setLoadState("loading");
    setError(null);
    try {
      const result = await getAppointmentAvailability(branchId, moduleCode, selectedDay);
      setSlots(result);
      setSelectedSlot(null);
      setLoadState("loaded");
    } catch (err) {
      setLoadState("error");
      setError(
        err instanceof ApiError
          ? err.problem.detail || err.problem.title || "La API rechazó la solicitud."
          : "No pudimos conectar con la API. Revisa que el backend esté corriendo.",
      );
    }
  }, [branchId, moduleCode, selectedDay]);

  useEffect(() => {
    void Promise.resolve().then(() => loadAvailability());
  }, [loadAvailability]);

  async function confirm() {
    if (!selectedSlot) return;
    setConfirming(true);
    setError(null);
    const idempotencyKey = getOrCreateIdempotencyKey(`hold:${branchId}:${moduleCode}:${selectedSlot.starts_at}`);
    try {
      const created = await createAppointmentHold(
        {
          branch_id: branchId,
          module_code: moduleCode,
          service_name: serviceName,
          starts_at: selectedSlot.starts_at,
          ends_at: selectedSlot.ends_at,
        },
        idempotencyKey,
      );
      setHold(created);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.problem.detail || err.problem.title || "No pudimos reservar ese horario."
          : "No pudimos conectar con la API para confirmar la cita.",
      );
    } finally {
      setConfirming(false);
    }
  }

  if (hold) {
    return (
      <PortalShell title="Cita confirmada" subtitle={`Módulo ${hold.module_code} · sucursal ${hold.branch_id}`}>
        <section className="mx-auto max-w-md rounded-2xl border border-success/35 bg-success/8 p-6 text-center shadow-soft">
          <StatusBadge tone="success">Hold creado</StatusBadge>
          <p className="mt-3 text-lg font-bold">
            {new Date(hold.starts_at).toLocaleDateString("es-BO", { day: "2-digit", month: "long" })}
            {" · "}
            {formatHour(hold.starts_at)}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Folio de la reserva: <span className="mono">{hold.appointment_id}</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Vence si no se confirma antes de {new Date(hold.hold_expires_at).toLocaleString("es-BO")}
          </p>
        </section>
      </PortalShell>
    );
  }

  return (
    <PortalShell
      title="Reservar cita presencial"
      subtitle={`Módulo ${moduleCode} · sucursal ${branchId}`}
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            1. Elige el día
          </h2>
          <ul className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-6">
            {days.map((day) => {
              const iso = isoDate(day);
              const activo = selectedDay === iso;
              return (
                <li key={iso}>
                  <button
                    onClick={() => setSelectedDay(iso)}
                    className={cn(
                      "w-full rounded-xl border px-2 py-3 text-center transition-colors",
                      activo ? "border-accent bg-accent/12 text-foreground" : "border-border bg-background",
                    )}
                  >
                    <span className="block text-xs text-muted-foreground">
                      {day.toLocaleDateString("es-BO", { weekday: "short" })}
                    </span>
                    <span className="mono block text-lg font-semibold">{day.getDate()}</span>
                  </button>
                </li>
              );
            })}
          </ul>

          <h2 className="mt-7 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            2. Elige la hora
          </h2>

          {loadState === "loading" ? (
            <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-5">
              {Array.from({ length: 6 }, (_, index) => (
                <div key={index} className="h-10 animate-pulse rounded-full bg-muted" />
              ))}
            </div>
          ) : null}

          {loadState === "error" ? (
            <div className="mt-3 rounded-xl border border-destructive/35 bg-destructive/8 p-4">
              <p className="text-sm font-semibold text-destructive">No pudimos cargar los horarios</p>
              <p className="mt-1 text-sm text-muted-foreground">{error}</p>
              <button
                onClick={() => void loadAvailability()}
                className="mt-3 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              >
                <RefreshCw className="size-4" /> Reintentar
              </button>
            </div>
          ) : null}

          {loadState === "loaded" && slots.length === 0 ? (
            <div className="mt-3 rounded-xl border border-dashed border-border p-6 text-center">
              <SearchX className="mx-auto size-5 text-muted-foreground" />
              <p className="mt-2 text-sm font-semibold">Sin cupos este día</p>
              <p className="mt-1 text-sm text-muted-foreground">Elige otro día para ver horarios.</p>
            </div>
          ) : null}

          {loadState === "loaded" && slots.length > 0 ? (
            <ul className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-5">
              {slots.map((slot) => {
                const activo = selectedSlot?.starts_at === slot.starts_at && slot.available;
                return (
                  <li key={slot.starts_at}>
                    <button
                      disabled={!slot.available}
                      onClick={() => setSelectedSlot(slot)}
                      className={cn(
                        "mono w-full rounded-full border px-2 py-2 text-sm transition-colors",
                        activo ? "border-accent bg-accent/12 font-semibold" : "border-border bg-background",
                        !slot.available &&
                          "cursor-not-allowed text-muted-foreground line-through opacity-60",
                      )}
                    >
                      {formatHour(slot.starts_at)}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </section>

        <section className="h-fit rounded-2xl border border-accent/30 bg-accent/8 p-5 shadow-soft lg:sticky lg:top-24">
          <StatusBadge tone="accent">Resumen de tu cita</StatusBadge>
          {selectedSlot ? (
            <>
              <p className="mt-4 text-xl font-bold">
                {new Date(selectedSlot.starts_at).toLocaleDateString("es-BO", {
                  day: "2-digit",
                  month: "long",
                })}{" "}
                · {formatHour(selectedSlot.starts_at)}
              </p>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li className="flex items-start gap-2.5">
                  <CalendarCheck className="mt-0.5 size-4 shrink-0 text-accent" />
                  <span>
                    {serviceName} · módulo <span className="mono">{moduleCode}</span>
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <MapPin className="mt-0.5 size-4 shrink-0 text-accent" />
                  <span>Sucursal #{branchId}</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Clock className="mt-0.5 size-4 shrink-0 text-accent" />
                  <span>
                    Duración:{" "}
                    {Math.round(
                      (new Date(selectedSlot.ends_at).getTime() -
                        new Date(selectedSlot.starts_at).getTime()) /
                        60000,
                    )}{" "}
                    minutos
                  </span>
                </li>
              </ul>
              {error ? (
                <p className="mt-4 rounded-lg border border-destructive/35 bg-destructive/8 p-3 text-sm text-destructive">
                  {error}
                </p>
              ) : null}
              <button
                disabled={confirming}
                onClick={() => void confirm()}
                className="mt-5 w-full rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {confirming ? "Confirmando…" : "Confirmar cita"}
              </button>
              <button
                onClick={() => setSelectedSlot(null)}
                className="mt-2 w-full rounded-full border border-border bg-card px-6 py-3 text-sm font-semibold transition-colors hover:bg-secondary"
              >
                Elegir otro horario
              </button>
            </>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">Elige un día y una hora disponibles.</p>
          )}
        </section>
      </div>
    </PortalShell>
  );
}
