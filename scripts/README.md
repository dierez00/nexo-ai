# Scripts

## Objetivo

Proveer comandos repetibles para arranque, seed, ingesta, evaluación y demo.

## Debe contener

Wrappers pequeños alrededor de CLIs públicas con `--help`, validación y códigos de salida.

## No debe contener

Lógica reusable, secretos ni acciones destructivas sin objetivo/confirmación explícitos.

## Convenciones

Idempotentes, fail-fast, ejecutables desde la raíz y compatibles con CI.

Responsable: Dani; Diego mantiene ingesta/evals.

## Ejemplos y tareas

Dependencias permitidas: CLIs públicas de los módulos y variables documentadas. Ejemplos: `run.sh`, `seed_demo.sh`, `ingest_demo.sh`, `eval.sh`. Implementar arranque de una línea y checks.

## Terminado

Los scripts documentan precondiciones, no ocultan errores y funcionan en un entorno limpio soportado.
