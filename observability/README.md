# Observabilidad y auditoría

## Objetivo

Reconstruir ejecuciones y medir operación sin filtrar secretos o PII.

## Debe contener

Taxonomía de eventos, logging JSONL, OpenTelemetry, dashboards, alertas y reglas de redacción.

## No debe contener

Payloads sensibles completos, tokens ni métricas numéricas inventadas por LLM.

## Convenciones

Propagar `trace_id`, `run_id`, `span_id`; eventos append-only y secuenciados; atributos de baja cardinalidad; masking antes de exportar.

## Dependencias y responsables

Depende de `contracts/events` y despliegue. Dani es responsable; Daher apoya auditoría/queries.

## Ejemplos y tareas

`otel/collector.yaml`, `dashboards/agent-latency.json`. Empezar con JSONL/eventos, añadir OTel y alertas en Pro.

## Terminado

Una solicitud se reconstruye por completo y sus logs se pueden compartir sin contenido sensible.
