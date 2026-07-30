# Datos y assets de demostración

## Objetivo

Versionar documentos, mocks y assets necesarios para una demo reproducible.

## Debe contener

Datos sintéticos, manifests, origen/licencia, checksum y fixtures pequeños revisables.

## No debe contener

PII real, credenciales, vector stores generados, dumps de producción ni material sin permiso.

## Convenciones

Marcar `synthetic: true`; separar fuente original de output generado; nombres por dominio/caso/versión.

Responsables: Daher para mocks y Diego para corpus; Cris para assets visuales.

## Dependencias, ejemplos, tareas y terminado

RAG, seeds y tests consumen esta carpeta; ningún servicio escribe aquí en producción. Ejemplos: `documents/vehiculos`, `mocks/twilio` y `assets/demo`. Crear corpus y fixtures de los cinco casos. La demo debe reconstruirse con estos datos y los servicios externos explícitamente documentados.
