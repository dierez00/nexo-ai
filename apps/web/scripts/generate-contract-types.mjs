/**
 * Genera tipos TypeScript a partir de los JSON Schema publicados en `contracts/`.
 *
 * `contracts/src/nexo_contracts/` (Pydantic) es la fuente de verdad;
 * `contracts/jsonschema/` y `contracts/events/` son artefactos derivados que
 * publica `python -m nexo_contracts.export`. Este script deriva un tercer
 * artefacto, los tipos TS de `apps/web`, a partir de esos mismos JSON Schema —
 * nunca se edita a mano. Es idempotente: dos corridas seguidas producen bytes
 * idénticos, por eso `frontend-contracts` en CI puede detectar drift con un
 * simple `git diff --exit-code` sobre `src/generated/contracts/`.
 */

import { compile } from "json-schema-to-typescript";
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..", "..", "..");
const contractsRoot = join(repoRoot, "contracts");
const outDir = join(here, "..", "src/generated/contracts");

const SOURCE_DIRS = [
  { dir: join(contractsRoot, "jsonschema"), skip: new Set(["index.json"]) },
  { dir: join(contractsRoot, "events"), skip: new Set() },
];

function loadContracts() {
  const contracts = [];
  for (const { dir, skip } of SOURCE_DIRS) {
    for (const file of readdirSync(dir)) {
      if (skip.has(file) || !file.endsWith(".v1.json")) continue;
      const contractName = file.replace(/\.v1\.json$/, "");
      const schema = JSON.parse(readFileSync(join(dir, file), "utf8"));
      contracts.push({ contractName, typeName: schema.title, schema });
    }
  }
  contracts.sort((a, b) => a.contractName.localeCompare(b.contractName));
  return contracts;
}

async function main() {
  mkdirSync(outDir, { recursive: true });

  const contracts = loadContracts();

  for (const { contractName, typeName, schema } of contracts) {
    const ts = await compile(schema, typeName, {
      additionalProperties: false,
      style: { singleQuote: false },
    });
    writeFileSync(join(outDir, `${contractName}.ts`), ts);
  }

  // Cada archivo también emite alias locales para sub-esquemas anónimos (p. ej.
  // un campo `date` genera `export type Date = ...`), que colisionarían entre sí
  // bajo un `export *`. El barrel solo reexporta el tipo principal de cada
  // contrato — el resto sigue siendo accesible importando el archivo directo.
  const indexLines = contracts.map(
    ({ contractName, typeName }) => `export type { ${typeName} } from "./${contractName}";`,
  );
  writeFileSync(join(outDir, "index.ts"), indexLines.join("\n") + "\n");

  const { contracts_schema_version: version } = JSON.parse(
    readFileSync(join(contractsRoot, "jsonschema", "index.json"), "utf8"),
  );
  writeFileSync(
    join(outDir, "version.ts"),
    `export const CONTRACTS_SCHEMA_VERSION = "${version}" as const;\n`,
  );

  console.log(`${contracts.length} contratos generados en ${outDir}`);
}

main();
