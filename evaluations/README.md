# Evaluaciones

## Objetivo

Medir calidad, seguridad y regresiones del sistema multiagente.

## Debe contener

Datasets, expected facts/tools, rúbricas, evaluadores deterministas, LLM-as-judge y reportes.

## No debe contener

PII real, prompts secretos ni resultados imposibles de reproducir.

## Convenciones

Cada caso tiene ID/versión; guardar configuración/seed; separar generación de evaluación; usar judge distinto y nunca como único gate.

## Dependencias y responsable

Depende de contratos y fixtures de dominio. Diego es responsable; cada integrante aporta aceptación de su módulo.

## Ejemplos y tareas

`datasets/capstone_v1.jsonl`, `rubrics/faithfulness.yaml`, `reports/`. Crear cinco casos, adversariales, baseline y judge Extremo.

## Terminado

Una orden produce métricas comparables y detecta regresiones conocidas en dominio, tool, fidelidad, permisos y A2UI.
