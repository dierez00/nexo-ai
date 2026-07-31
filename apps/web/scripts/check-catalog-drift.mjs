/**
 * Verifica que la copia del catálogo en `apps/web` siga siendo idéntica a la que
 * publica `a2ui/`.
 *
 * El catálogo es la allowlist del renderer: si se desincroniza, el cliente
 * empieza a rechazar componentes que el servidor sí emite (o peor, a aceptar
 * los que ya no debería). Que falle aquí es barato; que falle en producción no.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..", "..", "..");

const source = join(repoRoot, "a2ui/catalogs/citizen/v1/catalog.json");
const copy = join(here, "..", "src/features/a2ui/citizen-v1.catalog.json");

const read = (path) => readFileSync(path, "utf8");

if (read(source) !== read(copy)) {
  console.error("El catálogo A2UI de apps/web difiere del que publica a2ui/.");
  console.error(`  origen: ${source}`);
  console.error(`  copia:  ${copy}`);
  console.error("Copia el original y revisa los adaptadores antes de continuar.");
  process.exit(1);
}

console.log("Catálogo A2UI sincronizado con a2ui/catalogs/citizen/v1/catalog.json");
