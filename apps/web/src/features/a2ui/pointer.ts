/**
 * JSON Pointer (RFC 6901) para resolver bindings contra el data model.
 *
 * Un binding que todavía no resuelve devuelve `undefined` y el componente lo
 * trata como loading. **No** es un error fatal: el data model puede llegar
 * después del árbol, y tirar la superficie entera por un dato que aún no llegó
 * sería peor que dibujarla incompleta (`a2ui-v0.9.1.md`, §Datos).
 */

/** Un puntero válido es "" o empieza con "/". Todo lo demás es payload malformado. */
export function isValidPointer(pointer: string): boolean {
  if (pointer === "") return true;
  if (!pointer.startsWith("/")) return false;
  // `~` solo puede ir seguido de 0 o 1; cualquier otra cosa es un escape roto.
  return !/~(?![01])/.test(pointer);
}

function unescapeToken(token: string): string {
  // El orden importa: ~01 debe volverse ~1, no /. Por eso ~1 primero.
  return token.replace(/~1/g, "/").replace(/~0/g, "~");
}

/** Resuelve un puntero contra el documento. `undefined` si no existe la ruta. */
export function resolvePointer(document: unknown, pointer: string): unknown {
  if (!isValidPointer(pointer)) return undefined;
  if (pointer === "") return document;

  let current: unknown = document;
  for (const rawToken of pointer.slice(1).split("/")) {
    if (current === null || current === undefined) return undefined;
    const token = unescapeToken(rawToken);

    if (Array.isArray(current)) {
      // Un índice de array debe ser un entero sin ceros a la izquierda.
      if (!/^(0|[1-9][0-9]*)$/.test(token)) return undefined;
      current = current[Number(token)];
      continue;
    }
    if (typeof current !== "object") return undefined;

    // Solo propiedades propias: heredar de Object.prototype dejaría que un
    // puntero a "constructor" o "__proto__" devolviera algo.
    if (!Object.prototype.hasOwnProperty.call(current, token)) return undefined;
    current = (current as Record<string, unknown>)[token];
  }
  return current;
}

/**
 * Aplica un `updateDataModel` sobre el documento, devolviendo uno nuevo.
 *
 * El builder emite siempre `path: "/"`, pero el protocolo permite parches
 * parciales y el renderer tiene que soportarlos para las actualizaciones
 * incrementales que vienen después.
 */
export function applyAtPointer(document: unknown, pointer: string, value: unknown): unknown {
  if (pointer === "/" || pointer === "") return value;
  if (!isValidPointer(pointer)) return document;

  const tokens = pointer.slice(1).split("/").map(unescapeToken);
  const last = tokens.pop();
  if (last === undefined) return value;

  const root: Record<string, unknown> =
    typeof document === "object" && document !== null && !Array.isArray(document)
      ? { ...(document as Record<string, unknown>) }
      : {};

  let cursor: Record<string, unknown> = root;
  for (const token of tokens) {
    const next = cursor[token];
    const branch: Record<string, unknown> =
      typeof next === "object" && next !== null && !Array.isArray(next)
        ? { ...(next as Record<string, unknown>) }
        : {};
    cursor[token] = branch;
    cursor = branch;
  }
  cursor[last] = value;
  return root;
}
