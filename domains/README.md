# Dominios

## Objetivo

Reunir conocimiento, configuración y pruebas específicas de cada área sin duplicar infraestructura transversal.

## Debe contener

Manifest, prompts, fuentes, tools permitidas, reglas, fixtures y tests por dominio.

## No debe contener

Credenciales, framework del supervisor, adapters ni PII real.

## Convenciones

Slug estable; tool prefix propio; estructura equivalente; `domain.yaml` y fuentes versionadas. Las excepciones deben documentarse.

## Dependencias y mantenimiento

Solo APIs públicas de agentes, RAG, MCP y contratos. Cada dominio debe conservar
manifest, fuentes versionadas, skills, tools permitidas y pruebas reproducibles.

## Tareas

Vehículos y ayuntamiento/empresas en MVP; registro civil, salud y ganadería en Core. Ejemplos de archivos: `domain.yaml`, `sources.yaml`, `prompts/` y `fixtures/`.

## Terminado

Cada dominio resuelve su caso oficial con fuentes, preguntas mínimas, tools permitidas y fallback seguro.
