# Dominio: ayuntamiento y empresas

## Objetivo

Ordenar los permisos para abrir un negocio y calcular ruta, documentos, costos y citas.

## Contenido

Ejemplos: `domain.yaml`, `permit_graph.yaml`, prompts, fuentes, fixtures y tools `ayuntamiento.*`.

## Exclusiones

No dar asesoría legal/fiscal ni inventar permisos, dependencias o costos.

## Convenciones y dependencias

Representar dependencias como IDs estables; calcular totales en código. Depende del RAG municipal, estimador y tools de citas/solicitud.

Responsable: Diego; Daher apoya catálogo relacional y Dani acciones.

## Tareas iniciales

Implementar “taquería en Durango”, ordenar trámites, citar costos, detectar documentos, ofrecer cita e iniciar solicitud mock.

## Terminado

`CAP-EMP-01` produce flujo ordenado, todos los costos están respaldados y la acción confirmada devuelve folio.
