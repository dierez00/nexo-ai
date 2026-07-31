"use client";

/**
 * Adaptadores del catálogo ciudadano a los componentes que ya existen.
 *
 * Cada adaptador recibe props **ya resueltas** (los bindings se resolvieron en
 * `Surface.tsx`) y no ve el árbol ni el data model. No hay forma de que un
 * adaptador ejecute nada del payload: recibe datos, devuelve JSX.
 *
 * El builder de servidor emite listas de strings (`requisitos.items`,
 * `costos.lineas`) mientras las cards del chat esperan objetos. La traducción
 * vive aquí a propósito: cambiar las cards rompería el chat escrito a mano, y
 * cambiar el builder rompería el contrato con los otros canales.
 */

import type { ReactNode } from "react";
import { CheckCircle2, Circle, ExternalLink } from "lucide-react";

import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { cn } from "@/lib/utils";
import { asTone, type CatalogTone } from "./catalog";

/** Props resueltas de un componente, más sus hijos ya renderizados. */
export type AdapterProps = {
  properties: Record<string, unknown>;
  children: ReactNode[];
  /** Presente solo en los dos componentes interactivos del catálogo. */
  actionId?: string;
  onAction?: (actionId: string) => void;
  /** Bloquea la acción mientras se confirma (`cris_frontend.md` §13). */
  actionPending?: boolean;
};

type Adapter = (props: AdapterProps) => ReactNode;

// --- helpers de lectura tolerante ------------------------------------------
//
// Un binding que aún no resolvió llega como `undefined`. Eso es loading, no
// error: el data model puede llegar después del árbol.

function text(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return "";
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function records(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is Record<string, unknown> =>
      typeof item === "object" && item !== null && !Array.isArray(item),
  );
}

function number(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

/** El data model todavía no tiene el valor: hueco discreto, no error. */
function Loading({ label }: { label: string }) {
  return (
    <span
      aria-label={`${label}: cargando`}
      className="inline-block h-4 w-24 animate-pulse rounded bg-muted"
    />
  );
}

// --- tonos ------------------------------------------------------------------

const TONE_TO_BADGE: Record<CatalogTone, Tone> = {
  neutral: "neutral",
  info: "info",
  success: "success",
  warning: "warning",
  danger: "destructive",
};

const TONE_TO_SURFACE: Record<CatalogTone, string> = {
  neutral: "border-border bg-card",
  info: "border-info/30 bg-info/8",
  success: "border-success/35 bg-success/8",
  warning: "border-warning/40 bg-warning/10",
  danger: "border-destructive/35 bg-destructive/8",
};

// --- contenedores -----------------------------------------------------------

const GAP: Record<string, string> = { sm: "gap-2", md: "gap-4", lg: "gap-6" };
const ALIGN: Record<string, string> = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
};

const Column: Adapter = ({ properties, children }) => (
  <div
    className={cn(
      "flex flex-col",
      GAP[text(properties.gap)] ?? "gap-4",
      ALIGN[text(properties.align)] ?? "items-stretch",
    )}
  >
    {children}
  </div>
);

const Card: Adapter = ({ properties, children }) => {
  const tone = asTone(properties.tone);
  const title = text(properties.title);
  return (
    <section className={cn("rounded-xl border p-4", TONE_TO_SURFACE[tone])}>
      {title ? (
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {title}
        </p>
      ) : null}
      <div className={cn("space-y-3", title && "mt-3")}>{children}</div>
    </section>
  );
};

// --- texto y listas ---------------------------------------------------------

const Text: Adapter = ({ properties }) => {
  const value = properties.text;
  if (value === undefined) return <Loading label="Texto" />;
  const content = text(value);

  switch (text(properties.variant)) {
    case "h1":
      return <h2 className="text-xl font-bold tracking-tight">{content}</h2>;
    case "h2":
      return <h3 className="text-base font-semibold">{content}</h3>;
    case "caption":
      return <p className="text-xs text-muted-foreground">{content}</p>;
    default:
      return <p className="text-sm leading-relaxed">{content}</p>;
  }
};

const List: Adapter = ({ properties }) => {
  const items = strings(properties.items);
  if (properties.items === undefined) return <Loading label="Lista" />;
  if (items.length === 0) return null;

  const Tag = properties.ordered === true ? "ol" : "ul";
  return (
    <Tag
      className={cn(
        "space-y-1.5 text-sm text-muted-foreground",
        properties.ordered === true ? "list-decimal pl-5" : "list-disc pl-5",
      )}
    >
      {items.map((item, index) => (
        <li key={`${index}-${item}`}>{item}</li>
      ))}
    </Tag>
  );
};

// --- extensiones del catálogo ----------------------------------------------

const StatusBanner: Adapter = ({ properties }) => {
  const tone = asTone(properties.tone);
  // `message` puede venir como string o como lista de avisos: el builder pasa
  // `/avisos`, que es un array.
  const raw = properties.message;
  const messages = Array.isArray(raw) ? strings(raw) : raw === undefined ? [] : [text(raw)];

  return (
    <div className={cn("rounded-xl border p-4", TONE_TO_SURFACE[tone])}>
      <StatusBadge tone={TONE_TO_BADGE[tone]}>{text(properties.title)}</StatusBadge>
      {messages.length === 1 ? (
        <p className="mt-2 text-sm text-muted-foreground">{messages[0]}</p>
      ) : messages.length > 1 ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          {messages.map((message, index) => (
            <li key={`${index}-${message}`}>{message}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
};

const Checklist: Adapter = ({ properties }) => {
  const items = strings(properties.items);
  const progress = number(properties.progress);

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {text(properties.title) || "Requisitos"}
        </p>
        {progress !== undefined ? (
          <span className="mono shrink-0 text-xs text-muted-foreground">
            {Math.round(progress)}%
          </span>
        ) : null}
      </div>

      {progress !== undefined ? (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
          />
        </div>
      ) : null}

      {properties.items === undefined ? (
        <div className="mt-3">
          <Loading label="Requisitos" />
        </div>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((item, index) => {
            // El catálogo no marca cumplido por ítem: el progreso es del
            // conjunto. Se deriva de forma estable para no inventar estado.
            const done = progress !== undefined && (index + 1) * 100 <= progress * items.length;
            return (
              <li key={`${index}-${item}`} className="flex items-start gap-2.5 text-sm">
                {done ? (
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                ) : (
                  <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                )}
                <span className={cn(done ? "text-foreground" : "text-muted-foreground")}>
                  {item}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

const CostSummary: Adapter = ({ properties }) => {
  const lines = strings(properties.lines);
  const total = text(properties.total);

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {text(properties.title) || "Costos estimados"}
      </p>
      {properties.lines === undefined ? (
        <div className="mt-3">
          <Loading label="Costos" />
        </div>
      ) : (
        <ul className="mt-3 space-y-2 text-sm">
          {lines.map((line, index) => (
            <li key={`${index}-${line}`} className="text-muted-foreground">
              {line}
            </li>
          ))}
        </ul>
      )}
      {total ? (
        <div className="mt-3 flex items-baseline justify-between border-t border-border pt-3">
          <span className="text-sm font-semibold">Total estimado</span>
          <span className="mono text-base font-semibold">{total}</span>
        </div>
      ) : null}
    </div>
  );
};

const SourceList: Adapter = ({ properties }) => {
  const sources = records(properties.sources);
  if (properties.sources === undefined) return <Loading label="Fuentes" />;

  return (
    <div className="rail rounded-xl border border-border bg-card p-4">
      <span aria-hidden className="rail-node bg-accent" />
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        {text(properties.title) || "Fuentes oficiales citadas"}
      </p>
      <ul className="mt-2 space-y-2">
        {sources.map((source, index) => (
          <li key={`${index}-${text(source.fuente)}`}>
            <p className="mono text-sm font-medium">{text(source.fuente)}</p>
            <p className="mono text-xs text-muted-foreground">
              Corpus {text(source.version_corpus)}
            </p>
          </li>
        ))}
      </ul>
      {/* Sin URL navegable: el catálogo publica identificadores opacos, no rutas
          internas. El enlace real llegará cuando exista el portal documental. */}
      <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-muted-foreground">
        Identificadores auditables <ExternalLink className="size-3" aria-hidden />
      </p>
    </div>
  );
};

// --- componentes interactivos ----------------------------------------------

const SlotPicker: Adapter = ({ properties, actionId, onAction, actionPending }) => {
  const slots = strings(properties.slots);
  const selected = text(properties.selected);

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {text(properties.title) || "Elige tu cita"}
      </p>
      <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {slots.map((slot) => {
          const active = slot === selected;
          return (
            <li key={slot}>
              <button
                type="button"
                disabled={actionPending}
                aria-pressed={active}
                onClick={() => actionId && onAction?.(actionId)}
                className={cn(
                  "mono w-full rounded-xl border px-2 py-2.5 text-center text-sm transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "disabled:cursor-not-allowed disabled:opacity-60",
                  active
                    ? "border-accent bg-accent/12 font-semibold"
                    : "border-border bg-background",
                )}
              >
                {slot}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

const ConfirmButton: Adapter = ({ properties, actionId, onAction, actionPending }) => (
  <div className="rounded-xl border border-accent/40 bg-accent/8 p-4">
    <p className="text-xs font-semibold uppercase tracking-wide text-accent">
      Confirma antes de continuar
    </p>
    {text(properties.description) ? (
      <p className="mt-2 text-sm text-muted-foreground">{text(properties.description)}</p>
    ) : null}
    <button
      type="button"
      disabled={actionPending}
      onClick={() => actionId && onAction?.(actionId)}
      className={cn(
        "mt-4 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground",
        "transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2",
        "focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
      )}
    >
      {actionPending ? "Enviando…" : text(properties.label) || "Confirmar"}
    </button>
  </div>
);

/**
 * Registro cerrado. Un componente que no esté aquí no se dibuja — y el guard ya
 * lo rechazó antes de llegar. Registrar desde el payload es exactamente lo que
 * el catálogo cerrado existe para impedir.
 */
export const ADAPTERS: Readonly<Record<string, Adapter>> = Object.freeze({
  Column,
  Card,
  Text,
  List,
  Checklist,
  StatusBanner,
  CostSummary,
  SourceList,
  SlotPicker,
  ConfirmButton,
});
