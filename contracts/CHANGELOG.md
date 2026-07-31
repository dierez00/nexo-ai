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
