# Notas de implementación — Fase 1

La Fase 1 consolidó los recorridos MVP de vehículos y apertura de empresas,
RAG híbrido, herramientas MCP mock, confirmación idempotente, A2UI ciudadano,
eventos y pruebas E2E offline.

## Aprendizajes principales

- Los identificadores de fragmento deben conservar estabilidad semántica.
- La recuperación requiere umbrales comparables y casos fuera de alcance.
- Embeddings deterministas no deben simular semántica productiva.
- Las respuestas de tools deben filtrarse antes de convertirse en hechos.
- Los agentes transversales no deben repetirse en cada manifiesto de dominio.

## Próximos pasos

Paridad con persistencia PostgreSQL, cobertura frontend, CI separada para
integraciones, eventos SSE durables y adaptadores institucionales verificables.
