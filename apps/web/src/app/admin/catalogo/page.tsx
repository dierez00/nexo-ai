import type { Metadata } from "next";
import catalog from "../../../../public/fixtures/catalog/core.json";
import { AdminShell } from "@/components/nexo/admin-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";

export const metadata: Metadata = {
  title: "Catálogo Core — Nexo AI",
  description: "Dominios, agentes, skills y herramientas del catálogo central activo.",
  openGraph: {
    title: "Catálogo Core — Nexo AI",
    description: "Inventario operativo derivado de manifests y contratos versionados.",
  },
};

type CatalogKind = "domain" | "agent" | "tool" | "skill";

type CatalogEntity = {
  entity_id: string;
  kind: string;
  version: string;
  domain: string | null;
  title: string;
};

const labels: Record<CatalogKind, string> = {
  domain: "Dominio",
  agent: "Agente transversal",
  tool: "Herramienta",
  skill: "Skill operativa",
};

const tones: Record<CatalogKind, Tone> = {
  domain: "accent",
  agent: "info",
  tool: "success",
  skill: "primary",
};

function isVisibleKind(kind: string): kind is CatalogKind {
  return kind === "domain" || kind === "agent" || kind === "tool" || kind === "skill";
}

function description(entity: CatalogEntity) {
  if (entity.kind === "agent") {
    return "Agente transversal compartido; el dominio se parametriza desde el catálogo.";
  }
  if (entity.kind === "domain") {
    return "Namespace activo con fuentes, intenciones, tools y componentes permitidos.";
  }
  if (entity.kind === "skill") {
    return "Plan operativo versionado que no amplía permisos del dominio.";
  }
  return "Capacidad MCP tipada y filtrada por institución, rol, dominio y operación.";
}

export default function Page() {
  const items = (catalog.entities as CatalogEntity[])
    .filter((entity) => isVisibleKind(entity.kind))
    .sort((a, b) => a.kind.localeCompare(b.kind) || a.entity_id.localeCompare(b.entity_id));

  return (
    <AdminShell
      title="Catálogo"
      subtitle={`${catalog.version} · snapshot ${catalog.lifecycle}`}
      actions={<StatusBadge tone="success">{items.length} entidades activas</StatusBadge>}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {(Object.keys(labels) as CatalogKind[]).map((kind) => (
          <StatusBadge key={kind} tone={tones[kind]}>
            {labels[kind]} · {items.filter((item) => item.kind === kind).length}
          </StatusBadge>
        ))}
      </div>

      <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => {
          const kind = item.kind as CatalogKind;
          return (
            <li
              key={item.entity_id}
              className="rounded-2xl border border-border bg-card p-5 shadow-soft"
            >
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                <div className="min-w-0">
                  <p className="mono truncate text-sm font-semibold">{item.entity_id}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{labels[kind]}</p>
                </div>
                <StatusBadge tone={tones[kind]}>Activo</StatusBadge>
              </div>
              <div className="mt-3">
                <StatusBadge tone="neutral">Sin telemetría</StatusBadge>
              </div>
              <p className="mt-3 text-sm font-medium">{item.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{description(item)}</p>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="mono rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground">
                  {item.version}
                </span>
                <span className="text-xs text-muted-foreground">
                  {item.domain ?? "todos los dominios"}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </AdminShell>
  );
}
