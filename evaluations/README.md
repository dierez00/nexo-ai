# Evaluaciones Core

Este paquete contiene el dataset y los evaluadores deterministas de Fase 2. No
autoriza acciones ni modifica runs: recibe una observación congelada y la
compara con expectativas tipadas.

## Artefactos

- `datasets/capstone_v1.jsonl`: cinco casos oficiales, paráfrasis, negativos y
  ataques de prompt injection en mensaje, documento y respuesta de tool.
- `baselines/core_v1_observations.jsonl`: recording offline de los cinco casos
  oficiales, ligado al catálogo y a las versiones de skill.
- `src/nexo_evaluations/evaluator.py`: exact match de dominio/trámite, cobertura
  de fuentes, precisión de citas, tools, permisos, A2UI, escritura y preguntas.
- `reports/core_baseline_v1.{json,md}`: baseline comparable entre commits.

## Reproducir

```bash
uv run --frozen pytest evaluations/tests
uv run --frozen python evaluations/scripts/export_core_report.py
```

La validez de los recordings se sostiene además con los E2E offline de
`tests/e2e/`; el reporte no reemplaza esas pruebas.
