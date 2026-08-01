/**
 * Lifecycle de una superficie A2UI.
 *
 * Reglas del protocolo que se hacen cumplir aquí:
 *
 * - `createSurface` debe llegar antes que cualquier actualización.
 * - `surfaceId` y `catalogId` son inmutables durante la vida de la superficie.
 * - Un mensaje dirigido a otra superficie no se aplica.
 * - Ante un error de validación se **descarta la instancia completa**. No se
 *   conserva una superficie parcial: mezclaría estructura validada con
 *   estructura rechazada, que es exactamente el estado que un atacante querría.
 */

import { parseJsonl, validateCatalog, validateMessage, validateTree } from "./guard";
import { applyAtPointer } from "./pointer";
import { getCatalog } from "./catalog";
import type {
  A2UIAction,
  A2UIMessage,
  ProcessResult,
  ValidationError,
  WireComponent,
} from "./types";

function failure(errors: ValidationError[]): ProcessResult {
  return { ok: false, code: "VALIDATION_FAILED", errors };
}

/**
 * Procesa un lote de mensajes y devuelve la superficie lista para dibujar.
 *
 * Es intencionalmente una función pura y no una clase con estado: cada lote
 * arranca de cero, así que no existe la posibilidad de reutilizar un procesador
 * contaminado por un lote anterior que falló.
 */
export function processMessages(
  messages: A2UIMessage[],
  declaredActions: A2UIAction[] = [],
): ProcessResult {
  const errors: ValidationError[] = [];
  messages.forEach((message, index) => errors.push(...validateMessage(message, index)));
  if (errors.length > 0) return failure(errors);

  const first = messages[0];
  if (!first?.createSurface) {
    return failure([
      {
        rule: "missing_create_surface",
        detail: "el lote no abre con createSurface",
      },
    ]);
  }

  const catalogErrors = validateCatalog(first.createSurface.catalogId);
  // Sin catálogo coincidente no tiene sentido seguir: cualquier componente
  // sería «desconocido» y el informe sería ilegible.
  if (catalogErrors.length > 0) return failure(catalogErrors);
  const catalog = getCatalog(first.createSurface.catalogId);
  if (!catalog) {
    return failure([
      {
        rule: "unknown_catalog",
        detail: "la superficie declara un catálogo que este cliente no publica",
      },
    ]);
  }

  const surfaceId = first.createSurface.surfaceId;
  const catalogId = first.createSurface.catalogId;
  const actionIds = new Set(declaredActions.map((action) => action.actionId));

  let dataModel: unknown = {};
  let components: WireComponent[] | null = null;

  for (let index = 1; index < messages.length; index += 1) {
    const message = messages[index];

    if (message.createSurface) {
      return failure([
        {
          rule: "duplicate_create_surface",
          detail: "el lote intenta reabrir una superficie ya creada",
        },
      ]);
    }

    const target = message.updateDataModel?.surfaceId ?? message.updateComponents?.surfaceId;
    if (target !== surfaceId) {
      return failure([
        {
          rule: "surface_id_mismatch",
          detail: `el mensaje ${index} se dirige a otra superficie`,
        },
      ]);
    }

    if (message.updateDataModel) {
      dataModel = applyAtPointer(
        dataModel,
        message.updateDataModel.path,
        message.updateDataModel.value,
      );
    }
    if (message.updateComponents) {
      components = message.updateComponents.components;
    }
  }

  if (components === null) {
    return failure([
      { rule: "missing_components", detail: "el lote no declara un árbol de componentes" },
    ]);
  }

  const treeErrors = validateTree(components, actionIds, catalog);
  if (treeErrors.length > 0) return failure(treeErrors);

  return {
    ok: true,
    surface: {
      surfaceId,
      catalogId,
      components: new Map(components.map((component) => [component.id, component])),
      dataModel,
      actions: new Map(declaredActions.map((action) => [action.actionId, action])),
    },
  };
}

export type ProcessTimings = {
  /** Parseo del JSONL a objetos. */
  parseMs: number;
  /** Guard + lifecycle: todo lo que decide si la superficie se dibuja. */
  guardMs: number;
};

export type ProcessFromTextResult = ProcessResult & { timings: ProcessTimings };

/** Procesa JSONL crudo midiendo los tramos de parseo y validación. */
export function processJsonl(
  text: string,
  declaredActions: A2UIAction[] = [],
): ProcessFromTextResult {
  const parseStart = performance.now();
  const { messages, errors } = parseJsonl(text);
  const parseEnd = performance.now();

  if (errors.length > 0) {
    return {
      ...failure(errors),
      timings: { parseMs: parseEnd - parseStart, guardMs: 0 },
    };
  }

  const result = processMessages(messages, declaredActions);
  const guardEnd = performance.now();

  return {
    ...result,
    timings: { parseMs: parseEnd - parseStart, guardMs: guardEnd - parseEnd },
  };
}
