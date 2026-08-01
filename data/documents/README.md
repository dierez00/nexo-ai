# Documentos fuente de demostración

## Objetivo

Almacena exclusivamente corpus autorizado para RAG.

Cada documento debe acompañarse de manifest con institución, dominio, origen, versión, vigencia, fecha de verificación, licencia, responsable y checksum. No se aceptan archivos sin procedencia ni PII real.

Convención: `dominio/source_id/version/archivo`. La ingesta lee estos archivos; nunca escribe resultados aquí.

La metadata debe revisarse antes de activar una fuente. Ejemplo:
`vehiculos/src_licencias_demo/v3/requisitos.md`.

Dependencia permitida: el pipeline `rag` lee archivos/manifests; ninguna integración escribe aquí. Tarea inicial: dos corpus MVP y luego tres Core. Terminado cuando todos los chunks pueden rastrearse al archivo/manifest y una fuente vencida queda excluida.
