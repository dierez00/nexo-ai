"use client";

/**
 * Renderiza una superficie A2UI ya validada.
 *
 * Empieza en `root` y baja por `children`. Los bindings se resuelven contra el
 * data model justo antes de entregar las props al adaptador, así que ningún
 * adaptador ve el árbol ni el modelo completo.
 *
 * Si la superficie no valida, esto no se monta: el fallback lo decide quien
 * llama, con el resultado del processor.
 */

import { useMemo, type ReactNode } from "react";

import { A2UIBoundary } from "./Fallback";
import { resolvePointer } from "./pointer";
import { ADAPTERS } from "./registry";
import { isBinding, type Surface, type WireComponent } from "./types";

const STRUCTURAL_KEYS = new Set(["id", "component", "children", "actionId"]);

/** Separa las propiedades del componente de las claves estructurales. */
function propertiesOf(component: WireComponent, dataModel: unknown): Record<string, unknown> {
  const resolved: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(component)) {
    if (STRUCTURAL_KEYS.has(key)) continue;
    resolved[key] = isBinding(value) ? resolvePointer(dataModel, value.path) : value;
  }
  return resolved;
}

function renderNode(
  id: string,
  surface: Surface,
  onAction: ((actionId: string) => void) | undefined,
  actionPending: boolean,
  depth: number,
): ReactNode {
  // El guard ya rechazó los ciclos; esto es cinturón y tirantes por si el árbol
  // llegara a mutar entre validación y render.
  if (depth > 50) return null;

  const component = surface.components.get(id);
  if (!component) return null;

  const Adapter = ADAPTERS[component.component];
  if (!Adapter) return null;

  const children = (component.children ?? []).map((childId) =>
    renderNode(childId, surface, onAction, actionPending, depth + 1),
  );

  return (
    <Adapter
      key={component.id}
      properties={propertiesOf(component, surface.dataModel)}
      actionId={component.actionId ?? undefined}
      onAction={onAction}
      actionPending={actionPending}
    >
      {children}
    </Adapter>
  );
}

export function A2UISurface({
  surface,
  onAction,
  actionPending = false,
  traceId,
}: {
  surface: Surface;
  onAction?: (actionId: string) => void;
  actionPending?: boolean;
  traceId?: string;
}) {
  const tree = useMemo(
    () => renderNode("root", surface, onAction, actionPending, 0),
    [surface, onAction, actionPending],
  );

  return <A2UIBoundary traceId={traceId}>{tree}</A2UIBoundary>;
}
