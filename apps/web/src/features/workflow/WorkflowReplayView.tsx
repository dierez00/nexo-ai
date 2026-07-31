import { AdminShell } from "@/components/nexo/admin-shell";
import { Rail, RailItem } from "@/components/nexo/rail";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import type { WorkflowNode, WorkflowReplay, WorkflowStatus } from "./types";

const NODE_WIDTH = 180;
const NODE_HEIGHT = 72;
const COLUMN_GAP = 50;
const ROW_GAP = 38;
const COLUMNS = 3;

function toneFor(status: WorkflowStatus): Tone {
  if (status === "succeeded") return "success";
  if (status === "failed" || status === "denied") return "destructive";
  if (status === "started") return "warning";
  return "neutral";
}

function labelFor(status: WorkflowStatus) {
  const labels: Record<WorkflowStatus, string> = {
    started: "En curso",
    succeeded: "Completado",
    failed: "Falló",
    denied: "Denegado",
    skipped: "Omitido",
  };
  return labels[status];
}

function position(index: number) {
  return {
    x: 28 + (index % COLUMNS) * (NODE_WIDTH + COLUMN_GAP),
    y: 30 + Math.floor(index / COLUMNS) * (NODE_HEIGHT + ROW_GAP),
  };
}

function eventDetail(event: WorkflowReplay["timeline"][number]) {
  const outcome = event.data.outcome;
  const reason = event.data.reason;
  const node = event.data.node;
  const detail =
    typeof outcome === "string"
      ? outcome
      : typeof reason === "string"
        ? reason
        : typeof node === "string"
          ? node
          : event.actor_type;
  return `${event.actor_name} · ${detail}`;
}

function GraphNode({ node, index }: { node: WorkflowNode; index: number }) {
  const { x, y } = position(index);
  const color =
    node.status === "succeeded"
      ? "var(--color-success)"
      : node.status === "failed" || node.status === "denied"
        ? "var(--color-destructive)"
        : "var(--color-warning)";

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={NODE_WIDTH}
        height={NODE_HEIGHT}
        rx={12}
        fill="var(--color-background)"
        stroke="var(--color-border)"
      />
      <circle cx={x + 15} cy={y + 20} r={4} fill={color} />
      <text x={x + 28} y={y + 24} fontSize="12" fontWeight="600" fill="var(--color-foreground)">
        {node.label.slice(0, 24)}
      </text>
      <text x={x + 15} y={y + 45} fontSize="10.5" fill="var(--color-muted-foreground)">
        {node.kind} · sec. {node.started_sequence}
      </text>
      <text x={x + 15} y={y + 61} fontSize="10" fill="var(--color-muted-foreground)">
        {labelFor(node.status)}
        {node.duration_ms ? ` · ${node.duration_ms} ms` : ""}
      </text>
    </g>
  );
}

export function WorkflowReplayView({ replay }: { replay: WorkflowReplay }) {
  const byId = new Map(replay.nodes.map((node, index) => [node.node_id, index]));
  const rows = Math.max(1, Math.ceil(replay.nodes.length / COLUMNS));
  const height = 60 + rows * (NODE_HEIGHT + ROW_GAP);
  const failed = replay.nodes.filter(
    (node) => node.status === "failed" || node.status === "denied",
  ).length;

  return (
    <AdminShell
      title="Workflow"
      subtitle={`Replay ${replay.mapping_version} · catálogo ${replay.catalog_version ?? "sin versión"}`}
      actions={
        <StatusBadge tone={failed ? "destructive" : "success"}>
          {failed ? `${failed} nodo${failed === 1 ? "" : "s"} con fallo` : "Replay íntegro"}
        </StatusBadge>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-border px-5 py-3">
            <h2 className="truncate text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Grafo reconstruido
            </h2>
            <StatusBadge tone="accent">{replay.run_id}</StatusBadge>
          </div>
          <div className="overflow-x-auto p-4">
            <svg
              viewBox={`0 0 700 ${height}`}
              className="min-w-[700px]"
              style={{ height, width: 700 }}
              aria-label="Grafo reconstruido desde eventos"
              role="img"
            >
              {replay.edges.map((edge) => {
                const sourceIndex = byId.get(edge.source);
                const targetIndex = byId.get(edge.target);
                if (sourceIndex === undefined || targetIndex === undefined) return null;
                const source = position(sourceIndex);
                const target = position(targetIndex);
                const x1 = source.x + NODE_WIDTH;
                const y1 = source.y + NODE_HEIGHT / 2;
                const x2 = target.x;
                const y2 = target.y + NODE_HEIGHT / 2;
                return (
                  <path
                    key={`${edge.source}-${edge.target}`}
                    d={`M ${x1} ${y1} C ${x1 + 24} ${y1}, ${x2 - 24} ${y2}, ${x2} ${y2}`}
                    fill="none"
                    stroke="var(--color-accent)"
                    strokeWidth={1.5}
                    strokeOpacity={0.55}
                  />
                );
              })}
              {replay.nodes.map((node, index) => (
                <GraphNode key={node.node_id} node={node} index={index} />
              ))}
            </svg>
          </div>
          <div className="flex flex-wrap gap-2 border-t border-border px-5 py-3">
            <StatusBadge tone="neutral">Secuencia {replay.last_sequence}</StatusBadge>
            <StatusBadge tone="info">{replay.skill_id ?? "sin skill"}</StatusBadge>
            <span className="mono truncate text-xs text-muted-foreground">
              {replay.correlation_id}
            </span>
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Línea de eventos
          </h2>
          <Rail className="mt-5">
            {replay.timeline.map((event, index) => (
              <RailItem
                key={event.event_id}
                done={event.status === "succeeded" || event.status === "skipped"}
                active={index === replay.timeline.length - 1}
              >
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                  <p className="min-w-0 truncate text-sm font-semibold">{event.type}</p>
                  <span className="mono shrink-0 text-xs text-muted-foreground">
                    #{event.sequence}
                  </span>
                </div>
                <p className="mt-0.5 text-sm text-muted-foreground">{eventDetail(event)}</p>
                <StatusBadge tone={toneFor(event.status)} className="mt-2">
                  {labelFor(event.status)}
                </StatusBadge>
              </RailItem>
            ))}
          </Rail>
        </section>
      </div>
    </AdminShell>
  );
}
