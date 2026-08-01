# Notas de implementación — Fase 0

La Fase 0 estableció contratos tipados, puertos, dobles de prueba,
configuración validada y un grafo mínimo ejecutable offline.

## Decisiones relevantes

- Las dependencias se invierten mediante puertos propios.
- Los modelos falsos responden por propósito y no por coincidencia textual.
- Los payloads wire se validan como tipos seguros y excluyen campos internos.
- Las políticas de reintento, pausa y fallback viven en configuración versionada.
- A2UI usa un catálogo cerrado y fixtures JSONL válidos e inválidos.

## Deuda que continúa

OpenAPI generado, CI completa, persistencia durable, integración del stream con
la API y pruebas cruzadas entre paquetes.
