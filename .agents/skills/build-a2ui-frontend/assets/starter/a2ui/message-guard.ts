import { resolveAllowedA2UIUrl } from "./url-policy";

const ALLOWED_CATALOG_IDS = new Set([
  "urn:nexo-ia:a2ui:catalog:citizen:v1",
  "urn:nexo-ia:a2ui:catalog:admin:v1",
]);

const FORBIDDEN_KEYS = new Set([
  "className",
  "style",
  "dangerouslySetInnerHTML",
  "innerHTML",
  "html",
  "script",
  "handler",
  "module",
]);

function assertSafeValue(value: unknown, path: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertSafeValue(item, `${path}/${index}`));
    return;
  }
  if (!value || typeof value !== "object") {
    if (
      typeof value === "string" &&
      (value.toLowerCase().includes("<script") ||
        value.toLowerCase().includes("javascript:"))
    ) {
      throw new Error(`Unsafe executable content at ${path}`);
    }
    return;
  }

  for (const [key, child] of Object.entries(value)) {
    if (FORBIDDEN_KEYS.has(key) || /^on[A-Z_]/.test(key)) {
      throw new Error(`Unsafe A2UI property at ${path}/${key}`);
    }
    if (
      key.toLowerCase().endsWith("url") &&
      typeof child === "string" &&
      !resolveAllowedA2UIUrl(child)
    ) {
      throw new Error(`URL rejected by A2UI policy at ${path}/${key}`);
    }
    assertSafeValue(child, `${path}/${key}`);
  }
}

export function assertSafeA2UIMessages(messages: unknown): asserts messages is Array<
  Record<string, unknown>
> {
  if (!Array.isArray(messages) || messages.length === 0) {
    throw new Error("A2UI messages must be a non-empty array");
  }

  for (const [index, message] of messages.entries()) {
    if (!message || typeof message !== "object" || Array.isArray(message)) {
      throw new Error(`Invalid A2UI message at index ${index}`);
    }
    const record = message as Record<string, unknown>;
    if (record.version !== "v0.9.1") {
      throw new Error(`Unsupported A2UI version at index ${index}`);
    }

    const createSurface = record.createSurface;
    if (
      createSurface &&
      typeof createSurface === "object" &&
      !Array.isArray(createSurface)
    ) {
      const catalogId = (createSurface as Record<string, unknown>).catalogId;
      if (
        typeof catalogId !== "string" ||
        !ALLOWED_CATALOG_IDS.has(catalogId)
      ) {
        throw new Error(`Unknown A2UI catalog at index ${index}`);
      }
    }
    assertSafeValue(record, `/messages/${index}`);
  }
}
