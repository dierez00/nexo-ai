/**
 * Catálogo ciudadano cerrado, cargado desde el JSON que publica `a2ui/`.
 *
 * El JSON es copia de `a2ui/catalogs/citizen/v1/catalog.json`; el test de deriva
 * lo compara con el original para que una divergencia falle en CI y no en
 * producción. La allowlist es exhaustiva: un componente ausente de aquí no puede
 * aparecer en ninguna superficie válida.
 */

import catalogJson from "./citizen-v1.catalog.json";

type CatalogComponent = {
  name: string;
  schema_ref: string;
  allows_children: boolean;
  is_interactive: boolean;
};

type CatalogJson = {
  catalog_id: string;
  version: string;
  title: string;
  audience: string;
  components: CatalogComponent[];
  allowed_properties: Record<string, string[]>;
  allowed_tones: string[];
};

const catalog = catalogJson as CatalogJson;

export const CITIZEN_CATALOG_ID = catalog.catalog_id;
export const CATALOG_VERSION = catalog.version;

export const ALLOWED_TONES: ReadonlySet<string> = new Set(catalog.allowed_tones);

const byName = new Map(catalog.components.map((component) => [component.name, component]));

export const COMPONENT_NAMES: ReadonlySet<string> = new Set(byName.keys());

export const ALLOWED_PROPERTIES: ReadonlyMap<string, ReadonlySet<string>> = new Map(
  Object.entries(catalog.allowed_properties).map(([name, properties]) => [
    name,
    new Set(properties),
  ]),
);

export function findComponent(name: string): CatalogComponent | undefined {
  return byName.get(name);
}

export function allowsChildren(name: string): boolean {
  return byName.get(name)?.allows_children ?? false;
}

export function isInteractive(name: string): boolean {
  return byName.get(name)?.is_interactive ?? false;
}

/** Tonos del catálogo mapeados a los del design system. */
export type CatalogTone = "neutral" | "info" | "success" | "warning" | "danger";

export function asTone(value: unknown): CatalogTone {
  return typeof value === "string" && ALLOWED_TONES.has(value) ? (value as CatalogTone) : "neutral";
}
