# Citizen v1 congelado

El catálogo `urn:nexo-ia:a2ui:catalog:citizen:v1` quedó congelado el
2026-07-30 para conectar el flujo MVP sin reabrir el contrato del renderer.

## Fuente de verdad

- Protocolo: A2UI `v0.9.1`.
- Descriptor y propiedades: `catalog.json`.
- Contratos: JSON Schema A2UI v1 enumerados en `freeze.json`.
- Compatibilidad: fixtures válidos e inválidos de
  `a2ui/fixtures/citizen/v1/`.
- Huellas: SHA-256 en `freeze.json`.

## Regla de cambio

No se modifican componentes, propiedades, bindings, acciones, schemas ni
fixtures congelados bajo el mismo `catalog_id`.

Un cambio incompatible publica
`urn:nexo-ia:a2ui:catalog:citizen:v2`, conserva íntegro `v1` y añade sus propios
schemas, fixtures y manifiesto de congelación. Corregir una vulnerabilidad en
v1 exige documentar la excepción, rotar las huellas y revisar expresamente la
compatibilidad del renderer.

El trabajo restante no redefine A2UI: conecta
`RunResult.surface.messages` con el transporte y renderer existentes.

## Excepción registrada: rotación de huellas (2026-07-31)

`fix(contracts): publish real JSON Schemas instead of opaque stubs` (fd2c7cd)
reemplazó los siete JSON Schema A2UI referenciados por este freeze —eran stubs
opacos, no el contrato real— después de que `freeze.json` congelara sus
huellas. El catálogo, sus componentes, bindings, acciones y fixtures
(`catalog.json` y `a2ui/fixtures/citizen/v1/`) no cambiaron. Se rotaron las
siete huellas de `contracts/jsonschema/a2ui_*.v1.json` y
`catalog_descriptor.v1.json`/`channel_fallback.v1.json` en `freeze.json` para
reflejar el contenido real publicado; no hubo cambio de `catalog_id` ni de
`protocol_version`.
