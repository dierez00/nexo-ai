# Diego — agentes, RAG, MCP y orquestación

## 1. Objetivo general

Construir el núcleo inteligente como un grafo tipado, verificable y desacoplado de modelos y sistemas externos.

## 2. Responsabilidades

LangGraph, supervisor, agentes, model gateway/router, RAG, MCP, dominios, A2UI server-side, evals, guardrails y eventos.

## 3. Carpetas bajo responsabilidad

`agents`, `orchestration`, `rag`, `mcp`, `a2ui`, `domains`, `evaluations`; apoyo en `config` e `integrations/models`.

## 4. Tareas MVP

- RunState y modelo falso.
- Clasificador y dos navegadores.
- Verificador/estimador secuenciales.
- Agente transaccional mock y redactor cerrado.
- RAG híbrido y corpus.
- Server/tools MCP.
- Builder/validator A2UI.
- Eventos y fixtures.

## 5. Tareas Core

Cinco dominios, catálogo, tool permissions, workflow events, dataset de rúbrica y corpus versionado.

## 6. Tareas Pro

Router automático, MCP Mapper, contexto voz, formularios/admin A2UI y adapters reales junto con Dani.

## 7. Tareas Extremo

Paralelismo, contradicciones, mini-RAGs, LLM-as-judge, prompt assistant, doble verificación y routing por carga/salud.

## 8. Entregables concretos

Grafos, agentes, prompts/schemas, corpus/ingesta, server/tools MCP, catálogo A2UI, fixtures, datasets/evaluadores, eventos y documentación.

## 9. Dependencias con otros integrantes

- Dani: ejecución API, adapters y seguridad de canal.
- Daher: repositorios, vector schema, auditoría/checkpoints.
- Cris: renderer A2UI y event viewer.

## 10. Contratos de integración

Agentes Pydantic-only; sources por `source_id/fragment_id`; tool allowlist; redactor recibe `VerifiedFacts`; writes solo transaccional; eventos secuenciados; estado serializable e idempotente.

## 11. Riesgos y coordinación

Alucinaciones, prompts frágiles, cambios de proveedor, estado no serializable, tools peligrosas, corpus pobre, injection y judge sesgado. Priorizar gates deterministas y modelos falsos.

## 12. Pruebas a implementar

Modelos falsos, schemas, tool selection, source coverage, self-check, RAG recall/citation precision, reanudación, paralelo/merge, provider fallback, injection, A2UI validation y evals.

## 13. Criterios de aceptación

- ≥4/5 dominio/trámite.
- Claims críticos citados.
- Tool correcta y autorizada.
- Grafo reanudable sin duplicar efectos.
- 100% A2UI válido/fallback.
- Ningún agente no transaccional ejecuta writes.

## 14. Orden recomendado

Contratos/fixtures → fake model → RAG → agentes MVP → MCP → grafo → A2UI → dominios Core → router/Mapper → capacidades Extremo.

## 15. Checklist

- [ ] Inputs/outputs Pydantic.
- [ ] Prompts y versions.
- [ ] Budgets/timeouts/retries.
- [ ] Allowlists/permisos.
- [ ] Sources y vigencia.
- [ ] Autoverificación.
- [ ] Eventos/checkpoints.
- [ ] Tools mock/idempotencia.
- [ ] A2UI validation/fallback.
- [ ] Evals e injection.
- [ ] README/ADR.

## 16. Paralelismo y bloqueos

Agentes, prompts, corpus y tools avanzan con interfaces fake desde Fase 0. DB real depende de Daher; streaming/webhooks de Dani; renderer de Cris. Integración institucional queda bloqueada hasta contar con acceso y contrato, pero el mock conserva su wire shape.

## Funcionalidades compartidas

| Funcionalidad | Principal | Apoyo | Contrato | Entregable | Integración |
|---|---|---|---|---|---|
| Orquestación | Diego | Dani | RunRequest/Result/Event | Grafo invocable | MVP |
| A2UI generator | Diego | Cris | Catalog/JSONL | Builder + renderer | MVP |
| MCP/adapters | Diego | Dani | Tool schemas | Server + adapter | MVP/Pro |
| RAG/schema | Diego | Daher | Source/Chunk | Retriever + storage | MVP |
| Judge | Diego | Daher | JudgeResult | Eval/report | Extremo |
