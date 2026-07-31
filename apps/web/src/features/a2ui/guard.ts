/**
 * Guard de superficies: rechaza **antes** de renderizar, nunca durante.
 *
 * El validator de Diego (`a2ui/src/nexo_a2ui/validator.py`) es la autoridad en
 * servidor. Esto es la segunda barrera, no la primera: el cliente vuelve a
 * verificar porque el payload pudo cambiar en el camino, y porque un renderer
 * que confía en que alguien más ya validó es un renderer que ejecuta lo que le
 * manden el día que ese alguien falle.
 *
 * Los errores nombran la regla violada y, como mucho, el identificador del
 * catálogo implicado (nombre de componente o de propiedad) — igual que hace el
 * validator de servidor. Lo que **nunca** viaja en un error es el *valor*: la
 * URL, el texto o el objeto que disparó el rechazo. Ese detalle es justo lo que
 * un atacante usaría para afinar el siguiente intento, y además solo lo ve la
 * consola: el fallback que ve la persona usuaria no muestra ninguno de los dos.
 */

import {
  ALLOWED_PROPERTIES,
  CITIZEN_CATALOG_ID,
  COMPONENT_NAMES,
  allowsChildren,
  isInteractive,
} from "./catalog";
import { isValidPointer } from "./pointer";
import { A2UI_PROTOCOL_VERSION, isBinding } from "./types";
import type { A2UIMessage, ValidationError, WireComponent } from "./types";

const ROOT_ID = "root";

/**
 * Claves que no son propiedades sino vectores de ejecución. `on*` cubre
 * cualquier handler; el resto son las puertas conocidas a HTML y estilos
 * arbitrarios dentro de React.
 */
const FORBIDDEN_KEYS = new Set([
  "className",
  "style",
  "dangerouslySetInnerHTML",
  "innerHTML",
  "outerHTML",
  "html",
  "script",
  "srcDoc",
  "handler",
  "module",
  "ref",
  "key",
]);

/** Solo https. `javascript:`, `data:` y `file:` son los vectores clásicos. */
const ALLOWED_URL_SCHEMES = new Set(["https:"]);
const URL_PROPERTY_HINTS = ["url", "href", "link", "src"];

const STRUCTURAL_KEYS = new Set(["id", "component", "children", "actionId"]);

function looksLikeUrlProperty(key: string): boolean {
  const lower = key.toLowerCase();
  return URL_PROPERTY_HINTS.some((hint) => lower.endsWith(hint));
}

function isAllowedUrl(value: string): boolean {
  // Una ruta relativa del mismo origen es segura y no necesita esquema.
  if (value.startsWith("/") && !value.startsWith("//")) return true;
  try {
    return ALLOWED_URL_SCHEMES.has(new URL(value).protocol);
  } catch {
    return false;
  }
}

/**
 * Recorre un valor de propiedad buscando lo que nunca debe pasar: claves
 * prohibidas en objetos anidados, URLs con esquema no permitido y strings que
 * contienen marcado ejecutable.
 */
function scanValue(value: unknown, key: string, errors: ValidationError[], componentId: string) {
  if (typeof value === "string") {
    const lower = value.toLowerCase();
    if (lower.includes("<script") || lower.includes("javascript:")) {
      errors.push({
        componentId,
        rule: "executable_content",
        detail: `la propiedad ${r_safe(key)} contiene marcado ejecutable`,
      });
      return;
    }
    if (looksLikeUrlProperty(key) && !isAllowedUrl(value)) {
      errors.push({
        componentId,
        rule: "unsafe_url_scheme",
        detail: `la propiedad ${r_safe(key)} usa un esquema de URL no permitido`,
      });
    }
    return;
  }

  if (Array.isArray(value)) {
    for (const item of value) scanValue(item, key, errors, componentId);
    return;
  }

  if (typeof value === "object" && value !== null) {
    // Un binding es la única forma legítima de `{path}`.
    if (isBinding(value)) {
      if (!isValidPointer(value.path) || !value.path.startsWith("/")) {
        errors.push({
          componentId,
          rule: "invalid_binding",
          detail: `la propiedad ${r_safe(key)} no referencia un JSON Pointer absoluto`,
        });
      }
      return;
    }
    for (const [childKey, childValue] of Object.entries(value)) {
      if (FORBIDDEN_KEYS.has(childKey) || /^on[A-Z_]/.test(childKey)) {
        errors.push({
          componentId,
          rule: "forbidden_property",
          detail: `la propiedad ${r_safe(childKey)} no puede aparecer en una superficie`,
        });
        continue;
      }
      scanValue(childValue, childKey, errors, componentId);
    }
  }
}

/** Cita el nombre de una clave sin filtrar su valor. */
function r_safe(key: string): string {
  return `'${key.replace(/[^A-Za-z0-9_.-]/g, "")}'`;
}

function validateComponent(component: WireComponent, errors: ValidationError[]): void {
  const id = component.id;

  if (typeof id !== "string" || !/^[a-z][a-z0-9-]{0,62}$/.test(id)) {
    errors.push({ rule: "invalid_component_id", detail: "el identificador no tiene forma válida" });
    return;
  }

  if (!COMPONENT_NAMES.has(component.component)) {
    errors.push({
      componentId: id,
      rule: "component_not_in_catalog",
      detail: `el componente ${r_safe(String(component.component))} no está en el catálogo`,
    });
    return;
  }

  const children = component.children ?? [];
  if (children.length > 0 && !allowsChildren(component.component)) {
    errors.push({
      componentId: id,
      rule: "children_not_allowed",
      detail: `${r_safe(component.component)} no admite hijos`,
    });
  }

  if (component.actionId != null && !isInteractive(component.component)) {
    errors.push({
      componentId: id,
      rule: "action_on_non_interactive_component",
      detail: `${r_safe(component.component)} no puede disparar una acción`,
    });
  }

  const allowed = ALLOWED_PROPERTIES.get(component.component) ?? new Set<string>();
  for (const [key, value] of Object.entries(component)) {
    if (STRUCTURAL_KEYS.has(key)) continue;

    if (FORBIDDEN_KEYS.has(key) || /^on[A-Z_]/.test(key)) {
      errors.push({
        componentId: id,
        rule: "forbidden_property",
        detail: `la propiedad ${r_safe(key)} no puede aparecer en una superficie`,
      });
      continue;
    }
    if (!allowed.has(key)) {
      errors.push({
        componentId: id,
        rule: "unknown_property",
        detail: `${r_safe(component.component)} no admite la propiedad ${r_safe(key)}`,
      });
      continue;
    }
    scanValue(value, key, errors, id);
  }
}

/** Valida la forma de un mensaje suelto del JSONL. */
export function validateMessage(message: unknown, index: number): ValidationError[] {
  const errors: ValidationError[] = [];
  if (typeof message !== "object" || message === null || Array.isArray(message)) {
    errors.push({ rule: "malformed_message", detail: `el mensaje ${index} no es un objeto JSON` });
    return errors;
  }

  const record = message as Record<string, unknown>;
  if (record.version !== A2UI_PROTOCOL_VERSION) {
    errors.push({
      rule: "unsupported_protocol_version",
      detail: `el mensaje ${index} no declara ${A2UI_PROTOCOL_VERSION}`,
    });
    return errors;
  }

  const present = (["createSurface", "updateDataModel", "updateComponents"] as const).filter(
    (key) => record[key] != null,
  );
  if (present.length !== 1) {
    errors.push({
      rule: "message_must_carry_exactly_one_payload",
      detail: `el mensaje ${index} declara ${present.length} cargas útiles`,
    });
  }
  return errors;
}

/** Valida el catálogo declarado al abrir la superficie. */
export function validateCatalog(catalogId: unknown): ValidationError[] {
  if (catalogId !== CITIZEN_CATALOG_ID) {
    return [
      {
        rule: "unknown_catalog",
        detail: "la superficie declara un catálogo que este cliente no publica",
      },
    ];
  }
  return [];
}

/**
 * Valida el árbol completo: componentes, allowlist, unicidad, `root` y que cada
 * hijo referenciado exista.
 */
export function validateTree(
  components: WireComponent[],
  declaredActions: ReadonlySet<string>,
): ValidationError[] {
  const errors: ValidationError[] = [];

  if (components.length === 0) {
    errors.push({ rule: "empty_tree", detail: "el árbol no declara componentes" });
    return errors;
  }

  const seen = new Set<string>();
  for (const component of components) {
    if (seen.has(component.id)) {
      errors.push({
        componentId: component.id,
        rule: "duplicate_component_id",
        detail: "hay identificadores de componente duplicados",
      });
    }
    seen.add(component.id);
    validateComponent(component, errors);
  }

  if (!seen.has(ROOT_ID)) {
    errors.push({
      rule: "missing_root",
      detail: `el árbol debe declarar exactamente un componente '${ROOT_ID}'`,
    });
  }

  for (const component of components) {
    for (const child of component.children ?? []) {
      if (!seen.has(child)) {
        errors.push({
          componentId: component.id,
          rule: "unresolvable_child",
          detail: "referencia un hijo que no existe en el árbol",
        });
      }
    }
    if (component.actionId != null && !declaredActions.has(component.actionId)) {
      errors.push({
        componentId: component.id,
        rule: "action_not_declared",
        detail: "dispara una acción que la superficie no declaró",
      });
    }
  }

  // Un ciclo haría que el render no termine nunca.
  const index = new Map(components.map((component) => [component.id, component]));
  const state = new Map<string, "visiting" | "done">();
  const walk = (id: string): boolean => {
    const status = state.get(id);
    if (status === "done") return false;
    if (status === "visiting") return true;
    state.set(id, "visiting");
    for (const child of index.get(id)?.children ?? []) {
      if (index.has(child) && walk(child)) return true;
    }
    state.set(id, "done");
    return false;
  };
  if (seen.has(ROOT_ID) && walk(ROOT_ID)) {
    errors.push({ rule: "cyclic_tree", detail: "el árbol contiene un ciclo" });
  }

  return errors;
}

/** Parsea JSONL a mensajes, sin validar todavía la semántica. */
export function parseJsonl(text: string): { messages: A2UIMessage[]; errors: ValidationError[] } {
  const messages: A2UIMessage[] = [];
  const errors: ValidationError[] = [];

  text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line, index) => {
      try {
        messages.push(JSON.parse(line) as A2UIMessage);
      } catch {
        errors.push({ rule: "malformed_json", detail: `la línea ${index + 1} no es JSON válido` });
      }
    });

  return { messages, errors };
}
