import type { A2UISurface } from "@/generated/contracts";

const ADMIN_CATALOG_ID = "urn:nexo-ia:a2ui:catalog:admin:v1";
const SURFACE_ID = "surf_admin_mock";

type Intent =
  | "trend"
  | "domain"
  | "status"
  | "latency"
  | "actions"
  | "appointments"
  | "conversations"
  | "unsupported";

type Row = Record<string, string | number>;

const DOMAINS = ["Vehículos", "Empresas", "Registro civil", "Salud", "Ganadería"];
const STATUSES = ["succeeded", "partial", "waiting_confirmation", "failed"];
const ACTIONS = ["confirmed", "pending", "expired", "failed"];
const APPOINTMENTS = ["held", "confirmed", "released", "expired"];

function normalize(value: string) {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function classify(prompt: string): Intent {
  const value = normalize(prompt);
  if (value.includes("tendencia") || value.includes("diari") || value.includes("dia")) {
    return "trend";
  }
  if (value.includes("dominio") || value.includes("modulo") || value.includes("area")) {
    return "domain";
  }
  if (value.includes("accion")) return "actions";
  if (value.includes("cita")) return "appointments";
  if (value.includes("latencia") || value.includes("costo")) return "latency";
  if (value.includes("conversacion") || value.includes("chat")) return "conversations";
  if (value.includes("estado") || value.includes("status")) return "status";
  if (value.includes("tramite") || value.includes("run")) return "domain";
  return "unsupported";
}

function seedFor(prompt: string, rangeDays: number) {
  return [...prompt].reduce((sum, char) => sum + char.charCodeAt(0), rangeDays * 17);
}

function seriesFrom(labels: string[], key: string, seed: number): Row[] {
  return labels.map((label, index) => ({
    [key]: label,
    total: 18 + ((seed + index * 37) % 190),
  }));
}

function trend(seed: number, rangeDays: number): Row[] {
  const points = Math.min(Math.max(Math.round(rangeDays / 3), 7), 18);
  return Array.from({ length: points }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (points - index - 1) * 2);
    const total = 34 + ((seed + index * 19) % 86);
    return {
      date: date.toLocaleDateString("es-MX", { day: "2-digit", month: "short" }),
      total,
      exitosos: Math.round(total * (0.72 + ((seed + index) % 16) / 100)),
      derivados: Math.round(total * (0.08 + ((seed + index * 3) % 9) / 100)),
    };
  });
}

function table(columns: string[], rows: Row[]) {
  return {
    columns: columns.map((column) => ({ key: column, label: column.replace("_", " ") })),
    rows,
  };
}

function chartFor(intent: Intent, seed: number, rangeDays: number) {
  if (intent === "trend") {
    const rows = trend(seed, rangeDays);
    return {
      title: "Tendencia de trámites",
      description: "Serie generada desde la solicitud actual.",
      type: "area",
      xKey: "date",
      yKey: "total",
      series: [
        { key: "total", label: "Runs" },
        { key: "exitosos", label: "Exitosos" },
        { key: "derivados", label: "Derivados" },
      ],
      data: rows,
      table: table(["date", "total", "exitosos", "derivados"], rows),
    };
  }
  if (intent === "status") {
    const rows = seriesFrom(STATUSES, "status", seed);
    return {
      title: "Runs por estado",
      description: "Distribución por estado operativo.",
      type: "bar",
      xKey: "status",
      yKey: "total",
      series: [{ key: "total", label: "Runs" }],
      data: rows,
      table: table(["status", "total"], rows),
    };
  }
  if (intent === "latency") {
    const rows = [
      { metric: "latencia_ms", total: 620 + (seed % 920) },
      { metric: "costo_centavos_usd", total: 40 + (seed % 180) },
      { metric: "tokens_miles", total: 18 + (seed % 64) },
    ];
    return {
      title: "Latencia y costo",
      description: "Comparativo para revisar eficiencia.",
      type: "bar",
      xKey: "metric",
      yKey: "total",
      series: [{ key: "total", label: "Valor" }],
      data: rows,
      table: table(["metric", "total"], rows),
    };
  }
  if (intent === "actions") {
    const rows = seriesFrom(ACTIONS, "status", seed);
    return {
      title: "Acciones por estado",
      description: "Estados de confirmaciones y operaciones.",
      type: "donut",
      xKey: "status",
      yKey: "total",
      series: [{ key: "total", label: "Acciones" }],
      data: rows,
      table: table(["status", "total"], rows),
    };
  }
  if (intent === "appointments") {
    const rows = seriesFrom(APPOINTMENTS, "status", seed);
    return {
      title: "Citas por estado",
      description: "Ciclo de holds y confirmaciones.",
      type: "donut",
      xKey: "status",
      yKey: "total",
      series: [{ key: "total", label: "Citas" }],
      data: rows,
      table: table(["status", "total"], rows),
    };
  }
  if (intent === "conversations") {
    const rows = trend(seed + 11, rangeDays).map((row) => ({
      date: row.date,
      total: Math.round(Number(row.total) * 1.35),
      web: Math.round(Number(row.total) * 0.84),
      whatsapp: Math.round(Number(row.total) * 0.51),
    }));
    return {
      title: "Conversaciones por canal",
      description: "Serie por canal de entrada.",
      type: "line",
      xKey: "date",
      yKey: "total",
      series: [
        { key: "total", label: "Total" },
        { key: "web", label: "Web" },
        { key: "whatsapp", label: "WhatsApp" },
      ],
      data: rows,
      table: table(["date", "total", "web", "whatsapp"], rows),
    };
  }
  const rows = seriesFrom(DOMAINS, "domain", seed);
  return {
    title: "Trámites por dominio",
    description: "Distribución por dominio institucional.",
    type: "bar",
    xKey: "domain",
    yKey: "total",
    series: [{ key: "total", label: "Trámites" }],
    data: rows,
    table: table(["domain", "total"], rows),
  };
}

export function buildMockAdminChartSurface(prompt: string, rangeDays: number): A2UISurface {
  const intent = classify(prompt);
  const seed = seedFor(prompt, rangeDays);
  const chart = chartFor(intent, seed, rangeDays);
  const total = chart.data.reduce((sum, row) => sum + Number(row.total ?? 0), 0);
  const model = {
    intent: chart.title,
    window: `Últimos ${rangeDays} días`,
    summary: {
      runs: total.toLocaleString("es-MX"),
      latency: `${620 + (seed % 920)} ms`,
      cost: `$${(0.18 + (seed % 80) / 100).toFixed(2)} USD`,
    },
    chart,
    table: chart.table,
  };

  return {
    surface_id: SURFACE_ID,
    catalog_id: ADMIN_CATALOG_ID,
    channel: "web",
    actions: [],
    messages: [
      {
        version: "v0.9.1",
        createSurface: {
          surfaceId: SURFACE_ID,
          catalogId: ADMIN_CATALOG_ID,
          sendDataModel: true,
        },
      },
      {
        version: "v0.9.1",
        updateDataModel: {
          surfaceId: SURFACE_ID,
          path: "/",
          value: model,
        },
      },
      {
        version: "v0.9.1",
        updateComponents: {
          surfaceId: SURFACE_ID,
          components: [
            {
              id: "root",
              component: "Column",
              children: ["headline", "trace", "metric-runs", "metric-latency", "chart", "table"],
              properties: { align: "stretch", gap: "md" },
            },
            {
              id: "headline",
              component: "Text",
              properties: { text: { path: "/intent" }, variant: "h1" },
            },
            {
              id: "trace",
              component: "StatusBanner",
              properties: {
                title: "Interpretación",
                message: { path: "/window" },
                tone: "warning",
              },
            },
            {
              id: "metric-runs",
              component: "MetricCard",
              properties: {
                label: "Total",
                value: { path: "/summary/runs" },
                caption: "Generado desde la solicitud",
                tone: "success",
              },
            },
            {
              id: "metric-latency",
              component: "MetricCard",
              properties: {
                label: "Latencia",
                value: { path: "/summary/latency" },
                caption: { path: "/summary/cost" },
                tone: "info",
              },
            },
            {
              id: "chart",
              component: "ChartPanel",
              properties: {
                title: { path: "/chart/title" },
                description: { path: "/chart/description" },
                chartType: { path: "/chart/type" },
                data: { path: "/chart/data" },
                xKey: { path: "/chart/xKey" },
                yKey: { path: "/chart/yKey" },
                series: { path: "/chart/series" },
              },
            },
            {
              id: "table",
              component: "DataTable",
              properties: {
                title: "Datos",
                columns: { path: "/table/columns" },
                rows: { path: "/table/rows" },
                caption: "Agregados preparados para la ventana seleccionada.",
              },
            },
          ],
        },
      },
    ],
  };
}
