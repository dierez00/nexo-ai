# Changelog de contratos

Registra los cambios de los contratos compartidos de Nexo IA y el proceso para
aprobarlos (`DIE-F0-020`).

## Reglas de compatibilidad (`DIE-F0-007`)

Dentro de una versión mayor (`v1`) solo se admiten **cambios aditivos**:

- añadir un campo opcional con default;
- añadir un miembro nuevo a un enum;
- relajar una restricción (ampliar un rango, subir un `max_length`);
- añadir un contrato nuevo al registro.

Exigen **versión nueva** (`v2`), porque rompen a algún consumidor:

- eliminar o renombrar un campo;
- volver obligatorio un campo opcional;
- estrechar un tipo o un rango;
- eliminar o renombrar un miembro de enum;
- cambiar el significado de un campo conservando su nombre.

Una versión nueva no borra la anterior: ambas coexisten hasta que todos los
consumidores migren.

## Proceso de aprobación

1. Quien propone el cambio abre PR modificando **solo** los modelos Pydantic en
   `contracts/src/nexo_contracts/`.
2. Ejecuta `python -m nexo_contracts.export` para regenerar schemas, ejemplos y
   fixtures. Los artefactos generados nunca se editan a mano.
3. Ejecuta `pytest` — los contract tests fallan si hay desincronización entre
   modelo y artefacto publicado.
4. Añade la entrada correspondiente a este changelog, clasificada como aditiva o
   incompatible.
5. Aprueban los dueños de las fronteras afectadas: Dani (API, eventos, acciones),
   Daher (persistencia, RAG, checkpoints), Cris (A2UI, eventos de workflow) y
   Diego (agentes, orquestación, RAG, MCP).

Un cambio incompatible sin aprobación de todos los consumidores afectados no se
mezcla.

## v1 — 2026-07-30 — Fase 0

Primera publicación. Congela los contratos de la sección 5 del plan de Fase 0.

**Añadido**

- §5.1 ejecución: `RunRequest`, `RunState`, `RunResult`, `RunSnapshot`,
  `AgentTask`, `AgentResult`, `ActionRequest`, `ActionResult`.
- §5.2 hechos: `CandidateFact`, `VerifiedFact`, `VerifiedFacts`,
  `SourceCitation`, `Contradiction`, `Deduction`, `Estimate`.
- §5.3 RAG: `Source`, `Document`, `DocumentVersion`, `Chunk`, `CorpusVersion`,
  `RetrievalQuery`, `RetrievalResult`, `RetrievalResponse`, `IngestionResult`.
- §5.4 MCP: `ToolMetadata`, `ToolCall`, `ToolResult`, `ToolError`,
  `IntegrationDraft`, `MapperValidation`, `ControlledTestResult`, `Approval`,
  `PublishedToolVersion`.
- §5.5 A2UI: `CatalogDescriptor`, `ComponentDescriptor`, `A2UIMessage`,
  `A2UIComponent`, `A2UISurface`, `A2UIAction`, `A2UIValidationResult`,
  `ChannelFallback`.
- §5.6 modelos y evaluación: `ModelTask`, `ModelPolicy`, `ModelCapabilities`,
  `ModelCandidate`, `ModelDecision`, `ModelInvocation`, `SelfCheckResult`,
  `DeterministicEvaluationResult`, `JudgeRequest`, `JudgeResult`,
  `EvaluationReport`.
- §5.7 skills: `SkillManifest`.
- §5.8 eventos: `RunEvent`, `EventSequence`.
- Compartidos: `NormalizedError`.

**Decisiones que este changelog congela**

- Los modelos Pydantic de `contracts/src/nexo_contracts/` son la fuente de
  verdad; `contracts/jsonschema/`, `contracts/events/`, `contracts/examples/` y
  `domains/*/fixtures/` son artefactos generados.
- A2UI conserva el `camelCase` de su protocolo v0.9.1. Es la única excepción a
  la convención de wire format `snake_case`, y está acotada al paquete
  `nexo_contracts.a2ui`.
- Los campos marcados como internos (`nexo_visibility: internal`) existen en el
  estado serializado pero se eliminan en `model_dump_wire()` y no aparecen en
  `RunResult`.

## Fase 1 — cambios aditivos sobre `v1`

Todos compatibles según §1 de `docs/architecture/conventions.md`: campos
opcionales nuevos, miembros nuevos de enum y relajación de restricciones.
Ningún consumidor existente necesita cambiar.

| Contrato | Cambio | Motivo |
|---|---|---|
| `classification` (nuevo) | Contrato de salida del clasificador | Cierra el hueco H-08 de Fase 0; `FakeClassification` desaparece |
| `OperationalUrgency` (enum nuevo) | `routine` / `time_sensitive` / `urgent` | Urgencia **operativa**; en salud nunca describe una condición clínica |
| `VerifiedFact.supporting_tool_call_id` | Campo opcional nuevo | Un hecho crítico puede fundamentarse en una tool, no solo en un documento (H1-17) |
| `VerifiedFact` | La invariante de evidencia se relaja a «citación activa **o** tool» | Sin ello, el resultado de una escritura era inexpresable |
| `RunEvent.data` | Default explícito | El default vivía dentro de `SafePayload` e invisible para el análisis estático |
| `RunState.classification`, `retrieval_results`, `proposed_tools`, `tool_results` | Campos internos opcionales | El checkpoint conserva toda entrada necesaria para reanudar en otro proceso |
| `ActionRequest` | `cancelled` no exige consentimiento ni idempotency key | Cancelar antes de ejecutar no es autorizar una escritura |
| `catalog_entity_telemetry` (nuevo) | `CatalogEntityTelemetry` / `CatalogTelemetryState` | Estado observable de una entidad del catálogo durante una ventana temporal; existía en código pero nunca se había publicado su ejemplo ni documentado aquí |

## Fase 2 — herramientas de contrato

Sin cambios de forma en ningún contrato existente; corrige la publicación de
artefactos derivados y añade automatización.

- `contracts/jsonschema/*.v1.json` y `contracts/events/*.v1.json` ahora publican
  el schema real (`properties`, `required`, `type`) en vez de un stub opaco de 5
  líneas. La causa era que `schema_for()` generaba en modo `serialization`, que
  no puede introspeccionar un modelo con `model_serializer(mode="wrap")`;
  ahora genera en modo `validation` y `NexoModel.__get_pydantic_json_schema__`
  sigue excluyendo los campos `nexo_visibility: internal` del schema publicado.
- Se añadieron ejemplos inválidos para invariantes que no tenían cobertura:
  `approval`, `source`, `source_citation`, `tool_result`, `run_result`,
  `judge_result`, `deterministic_evaluation_result`, `controlled_test_result`,
  `ingestion_result`, `catalog_descriptor`, `component_descriptor`,
  `a2ui_component`, `a2ui_action`, `a2ui_validation_result`,
  `channel_fallback`.
- `apps/web` genera sus tipos TypeScript directamente desde
  `contracts/jsonschema/`/`contracts/events/` (`npm run generate:contracts`,
  fuente en `apps/web/scripts/generate-contract-types.mjs`), en vez de mirrors
  escritos a mano. Un job de CI (`frontend-contracts`) falla si el resultado
  publicado se desincroniza del schema.
