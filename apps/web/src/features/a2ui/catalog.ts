/**
 * Catálogo ciudadano cerrado, cargado desde el JSON que publica `a2ui/`.
 *
 * El JSON es copia de `a2ui/catalogs/citizen/v1/catalog.json`; el test de deriva
 * lo compara con el original para que una divergencia falle en CI y no en
 * producción. La allowlist es exhaustiva: un componente ausente de aquí no puede
 * aparecer en ninguna superficie válida.
 */

import catalogJson from "./citizen-v1.catalog.json";
import adminCatalogJson from "./admin-v1.catalog.json";

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
const adminCatalog = adminCatalogJson as CatalogJson;

export const CITIZEN_CATALOG_ID = catalog.catalog_id;
export const ADMIN_CATALOG_ID = adminCatalog.catalog_id;
export const CATALOG_VERSION = catalog.version;

export type CatalogRuntime = {
  catalogId: string;
  version: string;
  audience: string;
  componentNames: ReadonlySet<string>;
  allowedProperties: ReadonlyMap<string, ReadonlySet<string>>;
  allowedTones: ReadonlySet<string>;
  componentsByName: ReadonlyMap<string, CatalogComponent>;
};

function buildRuntime(source: CatalogJson): CatalogRuntime {
  const componentsByName = new Map(source.components.map((component) => [component.name, component]));
  return {
    catalogId: source.catalog_id,
    version: source.version,
    audience: source.audience,
    componentNames: new Set(componentsByName.keys()),
    allowedProperties: new Map(
      Object.entries(source.allowed_properties).map(([name, properties]) => [
        name,
        new Set(properties),
      ]),
    ),
    allowedTones: new Set(source.allowed_tones),
    componentsByName,
  };
}

const runtimes = [buildRuntime(catalog), buildRuntime(adminCatalog)] as const;
const byCatalogId = new Map(runtimes.map((runtime) => [runtime.catalogId, runtime]));
const citizenRuntime = byCatalogId.get(CITIZEN_CATALOG_ID)!;

export const ALLOWED_TONES: ReadonlySet<string> = new Set(
  runtimes.flatMap((runtime) => [...runtime.allowedTones]),
);

export const COMPONENT_NAMES: ReadonlySet<string> = citizenRuntime.componentNames;
export const ALLOWED_PROPERTIES: ReadonlyMap<string, ReadonlySet<string>> =
  citizenRuntime.allowedProperties;

export function getCatalog(catalogId: string): CatalogRuntime | undefined {
  return byCatalogId.get(catalogId);
}

export function findComponent(name: string): CatalogComponent | undefined {
  return citizenRuntime.componentsByName.get(name);
}

export function allowsChildren(name: string, runtime: CatalogRuntime = citizenRuntime): boolean {
  return runtime.componentsByName.get(name)?.allows_children ?? false;
}

export function isInteractive(name: string, runtime: CatalogRuntime = citizenRuntime): boolean {
  return runtime.componentsByName.get(name)?.is_interactive ?? false;
}

/** Tonos del catálogo mapeados a los del design system. */
export type CatalogTone = "neutral" | "info" | "success" | "warning" | "danger";

export function asTone(value: unknown): CatalogTone {
  return typeof value === "string" && ALLOWED_TONES.has(value) ? (value as CatalogTone) : "neutral";
}
