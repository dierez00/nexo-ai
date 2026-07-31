"use client";

import { useState } from "react";
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

export function AdminDashboard() {
  const [rango, setRango] = useState("7 días");

  return (
    <AdminShell
      title="Dashboard"
      subtitle="Operación de los cinco dominios habilitados"
      actions={<StatusBadge tone="success">Servicios operativos</StatusBadge>}
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
          24 jul – 30 jul 2026
        </span>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metricas.map((m) => (
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
            {dominios.map((d) => (
              <li key={d.nombre}>
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                  <span className="truncate text-sm">{d.nombre}</span>
                  <span className="mono shrink-0 text-sm font-medium">{d.total}</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-accent"
                    style={{ width: `${(d.total / 842) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </AdminShell>
  );
}
