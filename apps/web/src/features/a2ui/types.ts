/**
 * Tipos del wire A2UI v0.9.1, espejo de `contracts/src/nexo_contracts/a2ui.py`.
 *
 * Dos detalles del protocolo que no son obvios leyendo solo los nombres:
 *
 * 1. Las propiedades del componente viajan **aplanadas** junto a `id` y
 *    `component`, no anidadas bajo `properties`. Buscar `properties.text` no
 *    encuentra nada y la superficie sale vacía sin error.
 * 2. Cada línea del JSONL lleva **exactamente uno** de los tres mensajes; los
 *    nulos se omiten al serializar.
 */

export const A2UI_PROTOCOL_VERSION = "v0.9.1";

/** Referencia al data model por JSON Pointer absoluto. */
export type Binding = { path: string };

/** Un valor de propiedad: literal o binding. Nunca una función. */
export type PropertyValue = unknown;

export type WireComponent = {
  id: string;
  component: string;
  children?: string[];
  actionId?: string | null;
  /** Todo lo demás son propiedades del componente, aplanadas. */
  [property: string]: unknown;
};

export type CreateSurface = {
  surfaceId: string;
  catalogId: string;
  sendDataModel?: boolean;
};

export type UpdateDataModel = {
  surfaceId: string;
  path: string;
  value: unknown;
};

export type UpdateComponents = {
  surfaceId: string;
  components: WireComponent[];
};

export type A2UIMessage = {
  version: string;
  createSurface?: CreateSurface;
  updateDataModel?: UpdateDataModel;
  updateComponents?: UpdateComponents;
};

/** Acción opaca declarada por la superficie. El cliente nunca la interpreta. */
export type A2UIAction = {
  actionId: string;
  label: string;
  requiresConfirmation?: boolean;
};

/** Estado interno de una superficie ya validada y lista para dibujar. */
export type Surface = {
  surfaceId: string;
  catalogId: string;
  /** Árbol indexado por id; `root` siempre existe. */
  components: Map<string, WireComponent>;
  dataModel: unknown;
  actions: Map<string, A2UIAction>;
};

/**
 * Error de validación. `rule` describe la regla violada; nunca el valor que la
 * violó — un mensaje que incluye el payload filtra justo lo que un atacante
 * quería ver (`a2ui/src/nexo_a2ui/validator.py`).
 */
export type ValidationError = {
  rule: string;
  componentId?: string;
  detail: string;
};

export type ProcessResult =
  | { ok: true; surface: Surface }
  | { ok: false; code: "VALIDATION_FAILED"; errors: ValidationError[] };

export function isBinding(value: unknown): value is Binding {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    typeof (value as Binding).path === "string" &&
    Object.keys(value).length === 1
  );
}
