"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { tendencia } from "@/lib/mock";
import { cn } from "@/lib/utils";
import { apiFetch, type AdminCatalog, type MetricSet, type NexoConfigSummary } from "@/lib/api/client";

const rangos = ["Hoy", "7 días", "30 días", "Trimestre"];

const metricas = [
  {
    label: "Trámites atendidos",
    valor: "2.276",
    delta: "+12,4%",
    up: true,
    nota: "vs. semana anterior",
  },
  {
    label: "Tiempo promedio de resolución",
    valor: "1 m 34 s",
    delta: "-8,1%",
    up: false,
    nota: "mejor que la meta",
  },
  {
    label: "Tasa de éxito sin humano",
    valor: "94,2 %",
    delta: "+2,3%",
    up: true,
    nota: "meta institucional: 90 %",
  },
  {
    label: "Derivaciones a operador",
    valor: "132",
    delta: "+4,0%",
    up: true,
    nota: "5,8 % del total",
  },
];

const dominios = [
  { nombre: "Vehículos", total: 842, tone: "primary" as const },
  { nombre: "Empresas", total: 517, tone: "accent" as const },
  { nombre: "Registro civil", total: 431, tone: "info" as const },
  { nombre: "Salud", total: 298, tone: "success" as const },
  { nombre: "Ganadería", total: 188, tone: "warning" as const },
];

function formatNumber(value: number) {
  return new Intl.NumberFormat("es-MX").format(value);
}

function formatMs(value: number) {
  if (!value) return "0 ms";
  if (value < 1000) return `${Math.round(value)} ms`;
  return `${(value / 1000).toFixed(1)} s`;
}

export function AdminDashboard() {
  const [rango, setRango] = useState("7 días");
  const metrics = useQuery({
    queryKey: ["admin", "metrics", rango],
    queryFn: () => apiFetch<MetricSet>("/api/v1/admin/metrics"),
  });
  const catalog = useQuery({
    queryKey: ["admin", "catalog"],
    queryFn: () => apiFetch<AdminCatalog>("/api/v1/admin/catalog"),
  });
  const config = useQuery({
    queryKey: ["admin", "config"],
    queryFn: () => apiFetch<NexoConfigSummary>("/api/v1/admin/config"),
  });

  const realMetricas = metrics.data
    ? [
        {
          label: "Runs ejecutados",
          valor: formatNumber(metrics.data.runs.total),
          delta: `${formatNumber(metrics.data.conversations_total)} conversaciones`,
          up: true,
          nota: "ventana actual",
        },
        {
          label: "Latencia promedio",
          valor: formatMs(metrics.data.runs.avg_latency_ms),
          delta: `$${metrics.data.runs.total_cost_usd.toFixed(4)}`,
          up: false,
          nota: "costo total",
        },
        {
          label: "Acciones",
          valor: formatNumber(metrics.data.actions.total),
          delta: Object.keys(metrics.data.actions.by_status).join(", ") || "sin estados",
          up: true,
          nota: "por confirmar/ejecutadas",
        },
        {
          label: "Citas",
          valor: formatNumber(metrics.data.appointments.total),
          delta: Object.keys(metrics.data.appointments.by_status).join(", ") || "sin estados",
          up: true,
          nota: "holds y reservas",
        },
      ]
    : metricas;

  const realDominios = metrics.data
    ? Object.entries(metrics.data.runs.by_domain).map(([nombre, total]) => ({
        nombre,
        total,
        tone: "accent" as const,
      }))
    : dominios;

  const maxDominio = Math.max(1, ...realDominios.map((item) => item.total));
  const usingFallback = Boolean(metrics.error || catalog.error || config.error);

  return (
    <AdminShell
      title="Dashboard"
      subtitle="Operación de los cinco dominios habilitados"
      actions={
        <StatusBadge tone={usingFallback ? "warning" : "success"}>
          {usingFallback ? "Mostrando fallback" : "API conectada"}
        </StatusBadge>
      }
    >
      <div className="mb-5 flex flex-wrap gap-2">
        {rangos.map((r) => (
          <button
            key={r}
            onClick={() => setRango(r)}
            className={cn(
              "rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
              rango === r
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-card text-muted-foreground hover:text-foreground",
            )}
          >
            {r}
          </button>
        ))}
        <span className="mono self-center px-1 text-xs text-muted-foreground">
          {metrics.data
            ? `${new Date(metrics.data.window.start).toLocaleDateString("es-MX")} – ${new Date(
                metrics.data.window.end,
              ).toLocaleDateString("es-MX")}`
            : "24 jul – 30 jul 2026"}
        </span>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {realMetricas.map((m) => (
          <article
            key={m.label}
            className="rounded-2xl border border-border bg-card p-5 shadow-soft"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {m.label}
            </p>
            <p className="mono mt-3 text-2xl font-semibold">{m.valor}</p>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              {m.up ? (
                <ArrowUpRight className="size-3.5 text-success" />
              ) : (
                <ArrowDownRight className="size-3.5 text-success" />
              )}
              <span className="font-medium text-success">{m.delta}</span>
              <span className="text-muted-foreground">· {m.nota}</span>
            </div>
          </article>
        ))}
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <article className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
            <h2 className="truncate text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Tendencia de trámites
            </h2>
            <StatusBadge tone="accent">Diario</StatusBadge>
          </div>
          <div className="mt-5 h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={tendencia} margin={{ left: -20, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  stroke="var(--color-border)"
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis
                  dataKey="dia"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "var(--color-muted-foreground)", fontSize: 11 }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "var(--color-muted-foreground)", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "0.75rem",
                    fontSize: 12,
                    color: "var(--color-foreground)",
                  }}
                  labelStyle={{ color: "var(--color-muted-foreground)" }}
                />
                <Area
                  type="monotone"
                  dataKey="tramites"
                  name="Trámites"
                  stroke="var(--color-accent)"
                  strokeWidth={2}
                  fill="url(#g)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Volumen por dominio
          </h2>
          <ul className="mt-4 space-y-4">
            {realDominios.map((d) => (
              <li key={d.nombre}>
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                  <span className="truncate text-sm">{d.nombre}</span>
                  <span className="mono shrink-0 text-sm font-medium">{d.total}</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-accent"
                    style={{ width: `${(d.total / maxDominio) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="mt-4 grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Catálogo operativo
          </h2>
          <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Módulos</dt>
              <dd className="mono mt-1 text-lg font-semibold">
                {catalog.data?.modules.length ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Roles</dt>
              <dd className="mono mt-1 text-lg font-semibold">{catalog.data?.roles.length ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Permisos</dt>
              <dd className="mono mt-1 text-lg font-semibold">
                {catalog.data?.permissions.length ?? "—"}
              </dd>
            </div>
          </dl>
        </article>

        <article className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Configuración canónica
          </h2>
          <p className="mt-4 text-sm text-muted-foreground">
            {config.data
              ? `${Object.keys(config.data).length} bloques cargados desde /api/v1/admin/config.`
              : "Se mostrará cuando el backend responda con la configuración del tenant."}
          </p>
        </article>
      </section>
    </AdminShell>
  );
}
