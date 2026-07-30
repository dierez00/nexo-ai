"use client";

import { z } from "zod";
import { CommonSchemas } from "@a2ui/web_core/v0_9";
import { createComponentImplementation } from "@a2ui/react/v0_9";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { resolveAllowedA2UIUrl } from "./url-policy";

const toneSchema = z.enum(["neutral", "info", "success", "warning", "danger"]);
const toneClasses = {
  neutral: "border-l-border",
  info: "border-l-[hsl(var(--info))]",
  success: "border-l-[hsl(var(--success))]",
  warning: "border-l-[hsl(var(--warning))]",
  danger: "border-l-[hsl(var(--destructive))]",
} as const;

export const StatusBannerApi = {
  name: "StatusBanner",
  schema: z.object({
    title: CommonSchemas.DynamicString,
    message: CommonSchemas.DynamicString.optional(),
    tone: toneSchema.default("neutral"),
  }),
};

export const StatusBanner = createComponentImplementation(
  StatusBannerApi,
  ({ props }) => (
    <Alert
      role={props.tone === "danger" ? "alert" : "status"}
      data-tone={props.tone}
      className={`border-l-4 ${toneClasses[props.tone]}`}
    >
      <AlertTitle>{props.title}</AlertTitle>
      {props.message ? (
        <AlertDescription>{props.message}</AlertDescription>
      ) : null}
    </Alert>
  ),
);

export const SourceCitationApi = {
  name: "SourceCitation",
  schema: z.object({
    source: CommonSchemas.DynamicString,
    title: CommonSchemas.DynamicString,
    excerpt: CommonSchemas.DynamicString.optional(),
    url: CommonSchemas.DynamicString.optional(),
  }),
};

export const SourceCitation = createComponentImplementation(
  SourceCitationApi,
  ({ props }) => {
    const href = props.url ? resolveAllowedA2UIUrl(props.url) : undefined;
    return (
      <Card className="shadow-none">
        <CardHeader className="gap-2">
          <Badge className="w-fit" variant="secondary">
            {props.source}
          </Badge>
          <CardTitle className="text-base">{props.title}</CardTitle>
          {props.excerpt ? (
            <CardDescription>{props.excerpt}</CardDescription>
          ) : null}
        </CardHeader>
        {href ? (
          <CardContent>
            <Button asChild variant="link" className="h-auto p-0">
              <a href={href} rel="noreferrer" target="_blank">
                Consultar fuente
              </a>
            </Button>
          </CardContent>
        ) : null}
      </Card>
    );
  },
);

export const ChecklistApi = {
  name: "Checklist",
  schema: z.object({
    title: CommonSchemas.DynamicString,
    child: CommonSchemas.ComponentId,
    progress: CommonSchemas.DynamicNumber.optional(),
  }),
};

export const Checklist = createComponentImplementation(
  ChecklistApi,
  ({ props, buildChild }) => (
    <section aria-label={props.title} className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h3 className="font-semibold">{props.title}</h3>
        {typeof props.progress === "number" ? (
          <span className="font-[family-name:var(--nexo-font-data)] text-sm text-muted-foreground">
            {Math.round(props.progress)}%
          </span>
        ) : null}
      </div>
      {typeof props.progress === "number" ? (
        <Progress value={props.progress} aria-label={`Avance: ${props.progress}%`} />
      ) : null}
      {buildChild(props.child)}
    </section>
  ),
);

export const ConfirmationSummaryApi = {
  name: "ConfirmationSummary",
  schema: z.object({
    title: CommonSchemas.DynamicString,
    description: CommonSchemas.DynamicString.optional(),
    child: CommonSchemas.ComponentId,
    confirmLabel: CommonSchemas.DynamicString,
    action: CommonSchemas.Action,
  }),
};

export const ConfirmationSummary = createComponentImplementation(
  ConfirmationSummaryApi,
  ({ props, buildChild }) => (
    <Card className="border-primary/30 shadow-[var(--nexo-shadow-card)]">
      <CardHeader>
        <CardTitle>{props.title}</CardTitle>
        {props.description ? (
          <CardDescription>{props.description}</CardDescription>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-5">
        {buildChild(props.child)}
        <Button onClick={props.action}>{props.confirmLabel}</Button>
      </CardContent>
    </Card>
  ),
);

export const MetricCardApi = {
  name: "MetricCard",
  schema: z.object({
    label: CommonSchemas.DynamicString,
    value: CommonSchemas.DynamicString,
    detail: CommonSchemas.DynamicString.optional(),
    tone: toneSchema.default("neutral"),
  }),
};

export const MetricCard = createComponentImplementation(
  MetricCardApi,
  ({ props }) => (
    <Card data-tone={props.tone} className="min-w-0 shadow-none">
      <CardHeader className="pb-2">
        <CardDescription>{props.label}</CardDescription>
        <CardTitle className="font-[family-name:var(--nexo-font-data)] text-3xl tracking-tight">
          {props.value}
        </CardTitle>
      </CardHeader>
      {props.detail ? (
        <CardContent className="text-sm text-muted-foreground">
          {props.detail}
        </CardContent>
      ) : null}
    </Card>
  ),
);

const tableColumnSchema = z.object({
  key: z.string().regex(/^[a-z][a-zA-Z0-9_]{0,63}$/),
  label: z.string().min(1).max(80),
});

export const DataTableApi = {
  name: "DataTable",
  schema: z.object({
    caption: CommonSchemas.DynamicString,
    columns: z.array(tableColumnSchema).min(1).max(12),
    rows: CommonSchemas.DynamicValue,
  }),
};

function asRows(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) return [];
  return value
    .filter(
      (item): item is Record<string, unknown> =>
        typeof item === "object" && item !== null && !Array.isArray(item),
    )
    .slice(0, 250);
}

function displayCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  if (typeof value === "boolean") return value ? "Sí" : "No";
  return "Dato no disponible";
}

export const DataTable = createComponentImplementation(
  DataTableApi,
  ({ props }) => {
    const rows = asRows(props.rows);
    return (
      <div className="max-w-full overflow-x-auto rounded-lg border">
        <Table>
          <caption className="sr-only">{props.caption}</caption>
          <TableHeader>
            <TableRow>
              {props.columns.map((column) => (
                <TableHead key={column.key}>{column.label}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length ? (
              rows.map((row, index) => (
                <TableRow key={index}>
                  {props.columns.map((column) => (
                    <TableCell key={column.key}>
                      {displayCell(row[column.key])}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={props.columns.length}>
                  No hay datos para mostrar.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    );
  },
);

export const RunTimelineApi = {
  name: "RunTimeline",
  schema: z.object({
    title: CommonSchemas.DynamicString,
    child: CommonSchemas.ComponentId,
  }),
};

export const RunTimeline = createComponentImplementation(
  RunTimelineApi,
  ({ props, buildChild }) => (
    <section
      aria-label={props.title}
      className="border-l-2 border-[var(--nexo-trace-rail)] pl-5"
    >
      <h3 className="mb-4 font-semibold">{props.title}</h3>
      {buildChild(props.child)}
    </section>
  ),
);

const graphNodeSchema = z.object({
  id: z.string().min(1).max(128),
  label: z.string().min(1).max(160),
  status: z.enum(["pending", "running", "succeeded", "failed"]).optional(),
});

const graphEdgeSchema = z.object({
  from: z.string().min(1).max(128),
  to: z.string().min(1).max(128),
});

export const WorkflowGraphApi = {
  name: "WorkflowGraph",
  schema: z.object({
    title: CommonSchemas.DynamicString,
    nodes: CommonSchemas.DynamicValue,
    edges: CommonSchemas.DynamicValue,
  }),
};

function asGraphNodes(value: unknown): Array<z.infer<typeof graphNodeSchema>> {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    const parsed = graphNodeSchema.safeParse(item);
    return parsed.success ? [parsed.data] : [];
  }).slice(0, 100);
}

function asGraphEdges(value: unknown): Array<z.infer<typeof graphEdgeSchema>> {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    const parsed = graphEdgeSchema.safeParse(item);
    return parsed.success ? [parsed.data] : [];
  }).slice(0, 200);
}

export const WorkflowGraph = createComponentImplementation(
  WorkflowGraphApi,
  ({ props }) => {
    const nodes = asGraphNodes(props.nodes);
    const edges = asGraphEdges(props.edges);
    return (
      <section aria-label={props.title} className="space-y-4">
        <h3 className="font-semibold">{props.title}</h3>
        <ol className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {nodes.map((node) => (
            <li key={node.id} className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between gap-3">
                <span>{node.label}</span>
                {node.status ? (
                  <Badge variant="outline">{node.status}</Badge>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
        <p className="text-sm text-muted-foreground">
          {edges.length} conexiones en este flujo.
        </p>
      </section>
    );
  },
);
