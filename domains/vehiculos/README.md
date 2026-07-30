# Dominio: vehículos

## Objetivo

Resolver renovación de licencia, consulta de adeudo, módulos y citas para el recorrido MVP.

## Contenido

Ejemplos: `domain.yaml`, `prompts/`, `sources.yaml`, `fixtures/` y allowlist `vehiculos.*`.

## Exclusiones

No incluir multas, costos ni procesos no respaldados. No usar placas o identidades reales.

## Convenciones y dependencias

Dos intenciones deben conservarse separadas. Depende del RAG `vehiculos`, tools vehiculares, citas y contratos. Los cálculos monetarios son deterministas.

Responsable: Diego; Dani apoya citas/adapters y Daher fixtures.

## Tareas iniciales

Clasificar doble intención, recuperar requisitos, consultar adeudo mock, localizar módulo, ofrecer/confirmar cita y mostrar folio.

## Terminado

`CAP-VEH-01` completa E2E, cada claim crítico tiene fuente y repetir confirmación no crea otra cita.
