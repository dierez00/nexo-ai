# Fase 0 — hallazgos, decisiones y deuda técnica

> **Autor:** Diego. **Fecha:** 2026-07-30.
> **Alcance:** implementación de la Fase 0 de
> [`diego_plan_implementacion_hasta_extremo.md`](./diego_plan_implementacion_hasta_extremo.md).
>
> Formato por hallazgo: descripción, ubicación, impacto y acción tomada o
> recomendada.

## Índice

- [1. Bugs encontrados y corregidos](#1-bugs-encontrados-y-corregidos)
- [2. Inconsistencias y ambigüedades del plan](#2-inconsistencias-y-ambigüedades-del-plan)
- [3. Decisiones tomadas](#3-decisiones-tomadas)
- [4. Deuda técnica asumida](#4-deuda-técnica-asumida)
- [5. Mejoras detectadas fuera de alcance](#5-mejoras-detectadas-fuera-de-alcance)
- [6. Requiere decisión antes de Fase 1](#6-requiere-decisión-antes-de-fase-1)

---

## 1. Bugs encontrados y corregidos

### H-01 — El checkpoint quedaba una posición atrás de la traza de eventos

**Descripción.** `_persist()` guardaba el `RunState` y **después** emitía el
evento `checkpoint.saved`. El estado persistido conservaba por tanto un
`event_cursor` con una unidad menos que los eventos realmente emitidos. Al
reanudar, el grafo cargaba ese estado y emitía el siguiente evento con una
`sequence` ya ocupada, y el sink la rechazaba.

**Ubicación.** `orchestration/src/nexo_orchestration/graph/minimal.py:150`
(`_persist`), detectado por
`orchestration/tests/test_graph.py:83` (`test_resume_continues_the_event_sequence`).

**Impacto.** Alto y silencioso en Fase 0, crítico en Fase 1: toda reanudación
después de una confirmación habría fallado con un error de secuencia, es decir,
exactamente el flujo central del MVP (`CAP-VEH-01` y `CAP-EMP-01`). No se
manifiesta en el camino feliz, solo al reanudar.

**Acción tomada.** Se invirtió el orden: el `checkpoint_id` se obtiene de la
`IdFactory` inyectada, se emite `checkpoint.saved` y **después** se persiste el
estado que ya incluye ese evento. La firma del puerto cambió a
`save(state, *, node, checkpoint_id)`, lo que además hace reproducibles los
identificadores de checkpoint. Se añadió
`test_checkpoint_cursor_matches_the_emitted_events` como prueba de regresión y
se documentó el invariante en el
[ADR 0002](../adr/0002-grafo-langgraph-estado-y-checkpoints.md).

### H-02 — La prueba de PII marcaba los ejemplos deliberadamente inválidos

**Descripción.** La prueba de seguridad que recorre los fixtures buscando
secretos y PII incluía `contracts/examples/invalid/`, cuyos payloads contienen
`api_key` y `telefono` precisamente porque su propósito es demostrar que se
rechazan.

**Ubicación.** `contracts/tests/test_examples.py:88`.

**Impacto.** Bajo, pero del tipo que erosiona una suite: una prueba de seguridad
que falla siempre acaba desactivándose.

**Acción tomada.** El escaneo se acotó a `examples/valid/` y a
`domains/*/fixtures/`, con la exclusión documentada en el docstring.

---

## 2. Inconsistencias y ambigüedades del plan

### H-03 — «Implementar conceptualmente» contra el gate de salida

**Descripción.** `DIE-F0-038` (§7.5) pide «implementar **conceptualmente** la
ruta `start → classify_fake → finalize_fake`», mientras el objetivo (§7.1) y el
gate (§7.9) exigen que «un `RunRequest` atraviese un grafo mínimo con modelo
falso» y que «un modelo falso recorra el grafo mínimo». Un diseño conceptual no
satisface un gate ejecutable.

**Ubicación.** Plan §7.5 línea 303 contra §7.1 línea 238 y §7.9 línea 325.

**Impacto.** Medio: determina si Fase 0 entrega código ejecutable o solo diseño.

**Resolución.** Se resolvió a favor del gate —criterio más estricto y
verificable— con confirmación explícita tuya. El grafo está implementado sobre
LangGraph y se ejercita en la suite. **Recomendación:** corregir la redacción de
`DIE-F0-038` en el plan para eliminar la contradicción.

### H-04 — El plan no ubica el paquete Pydantic compartido

**Descripción.** `DIE-F0-011` exige especificar todos los contratos de §5 en
Pydantic, pero ni el plan ni la arquitectura dicen en qué paquete Python viven.
El árbol de §6 muestra `contracts/` con `openapi/`, `jsonschema/`, `events/` y
`examples/` —ningún `src/`— y §6.1 asigna la carpeta a Dani.

**Ubicación.** Plan §5 línea 143; arquitectura §6 líneas 394-399 y §6.1 línea 463.

**Impacto.** Alto: define la topología de dependencias de todo el núcleo.

**Resolución.** Decidido contigo: `contracts/src/nexo_contracts/`. Lo respalda
`contracts/README.md`, que ya declara «Pydantic/OpenAPI será la fuente del
cliente TypeScript generado», y lo exige la prohibición de «tipos duplicados
manualmente» del mismo README. **Requiere ratificación de Dani**, que custodia
la carpeta (ver §6).

### H-05 — A2UI usa `camelCase` y el wire format global exige `snake_case`

**Descripción.** `contracts/README.md` fija «wire format `snake_case`» sin
excepciones, pero A2UI v0.9.1 define sus mensajes en `camelCase`
(`createSurface`, `surfaceId`, `catalogId`), como confirman los fixtures de la
skill `build-a2ui-frontend`.

**Ubicación.** `contracts/README.md` §Convenciones contra
`.agents/skills/build-a2ui-frontend/assets/fixtures/citizen-license.valid.jsonl`.

**Impacto.** Medio: sin resolverlo, cada equipo habría inventado su propia
traducción y los fixtures no habrían sido intercambiables.

**Acción tomada.** Se respeta el protocolo tal cual. Los campos Python siguen en
`snake_case` y el alias traduce; la excepción está acotada al paquete
`nexo_contracts.a2ui` y registrada en
[`conventions.md` §4](../architecture/conventions.md) y en el
[ADR 0006](../adr/0006-a2ui-091-catalogo-cerrado-y-fallback.md).

### H-06 — El prefijo de tool no coincide con el slug del dominio

**Descripción.** Los cinco namespaces son `vehiculos`, `ayuntamiento_empresas`,
`registro_civil`, `salud` y `ganaderia`, pero las tools del MVP se llaman
`ayuntamiento.consultar_uso_suelo`, `ayuntamiento.registrar_solicitud`, etc.
El prefijo `ayuntamiento` no es el slug `ayuntamiento_empresas`.

**Ubicación.** Plan §2.3 línea 56 contra §8.11 líneas 455-459; arquitectura
§7.10 («tool prefix `ayuntamiento`»).

**Impacto.** Bajo si se decide, alto si cada quien asume algo distinto: un
prefijo divergente rompe el filtrado por dominio en el registry.

**Acción tomada.** Se conserva el prefijo corto `ayuntamiento` porque así están
nombradas las tools en ambas fuentes. La correspondencia dominio → prefijo está
codificada en `ToolMetadata`: declarar un dominio y usar otro prefijo falla en
validación. Tabla en [`conventions.md` §5](../architecture/conventions.md).

### H-07 — `RunState` referencia una estimación sin contrato definido

**Descripción.** §5.1 lista `estimación` entre los campos de `RunState`, pero
§5 no define ningún contrato de estimación; el estimador aparece hasta F1.7.
Dejar el campo sin tipo habría violado `DIE-F0-012` (nada de tipos libres).

**Ubicación.** Plan §5.1 línea 148 contra §8.9.

**Acción tomada.** Se creó un contrato `Estimate`/`EstimateStep` mínimo
(`contracts/src/nexo_contracts/estimation.py`) con las dos invariantes que ya se
pueden congelar: el total se suma en código sobre unidades menores y el DAG de
dependencias no admite ciclos. Las reglas de cálculo quedan para F1.7.

### H-08 — Falta un contrato de clasificación para el nodo `classify_fake`

**Descripción.** El grafo mínimo necesita validar la salida del modelo falso,
pero el contrato del clasificador se define en F1.4, no en §5.

**Acción tomada.** Se declaró `FakeClassification` **local a la orquestación**
(`graph/minimal.py`), explícitamente marcado como andamiaje de Fase 0, en lugar
de contaminar el registro de contratos publicados con un placeholder. Cuando
llegue F1.4, el nodo pasará a validar contra el contrato real y
`FakeClassification` desaparece.

---

## 3. Decisiones tomadas

| # | Decisión | Motivo | Dónde queda registrada |
|---|---|---|---|
| D-01 | Contratos Pydantic en `contracts/src/nexo_contracts/`; el resto se genera | El README ya declara Pydantic como fuente y prohíbe duplicar tipos | `contracts/CHANGELOG.md` |
| D-02 | LangGraph desde Fase 0, envuelto por `GraphState` local | El contrato publicado no debe conocer el framework | [ADR 0002](../adr/0002-grafo-langgraph-estado-y-checkpoints.md) |
| D-03 | Checkpoints por puerto propio, no por el checkpointer de LangGraph | Lo que se persiste es `RunState`, que es lo que Daher almacenará | [ADR 0002](../adr/0002-grafo-langgraph-estado-y-checkpoints.md) |
| D-04 | Puertos asíncronos para todo lo que hará I/O | Un puerto síncrono forzaría adapters bloqueantes en Fase 1 | `orchestration/src/nexo_orchestration/ports/` |
| D-05 | Cada puerto vive en el módulo dueño de su capacidad | `rag` posee retrieval, `mcp` posee tools; evita invertir dependencias | `docs/architecture/module_ownership.md` §4 |
| D-06 | `mcp` declara su propio `ClockLike` estructural | Importar el `Clock` de `orchestration` invertiría la dependencia | `mcp/src/nexo_mcp/testing/executor.py` |
| D-07 | El modelo falso responde por `purpose`, no por texto del prompt | `DIE-F0-022`; el matching por texto se rompe al mejorar un prompt | `orchestration/src/nexo_orchestration/testing/fake_model.py` |
| D-08 | Campos internos marcados con `nexo_visibility` y filtrados en `model_dump_wire()` | `DIE-F0-013`; `RunResult.from_state` además enumera campo por campo | `contracts/src/nexo_contracts/base.py` |
| D-09 | Serializabilidad garantizada por tipos (`SafePayload`), no por convención | Un objeto vivo falla en validación, no en el checkpoint | `contracts/src/nexo_contracts/safety.py` |
| D-10 | `halt` / `partial` / `fallback` codificados en `config/policies.yaml` | `DIE-F0-010`; el grafo consulta la regla en vez de improvisarla por nodo | `contracts/src/nexo_contracts/config.py` |
| D-11 | `venv` + `pip` en lugar de `uv` | `uv` no está instalado; equivalente para Fase 0 (ver TD-01) | Este documento |
| D-12 | `A2UIComponent` aplana propiedades al serializar | Los fixtures salen con la forma del protocolo, sin traducción en el renderer | [ADR 0006](../adr/0006-a2ui-091-catalogo-cerrado-y-fallback.md) |
| D-13 | Ruff ignora `RUF001`-`RUF003` | El código está en español; los acentos y «×» no son ambigüedades tipográficas | `pyproject.toml` |

---

## 4. Deuda técnica asumida

### TD-01 — `uv` no está instalado; no hay lockfile

**Descripción.** La arquitectura §5 elige `uv` como tooling y §16.2 lista
`uv.lock` entre los archivos de Fase 0/MVP. El entorno no lo tenía, así que se
usó `venv` + `pip`. No existe lockfile, por lo que las instalaciones no son
todavía bit a bit reproducibles.

**Impacto.** Medio. No afecta a la corrección del código, pero CI no puede
garantizar el mismo árbol de dependencias entre corridas.

**Acción recomendada.** Instalar `uv`, generar `uv.lock` y declarar el workspace
antes de configurar CI. Es trabajo de Dani según §16.2 y `scripts/README.md`.

### TD-02 — Los dobles de RAG no sirven para medir calidad

**Descripción.** `DeterministicEmbeddings` deriva vectores de un hash y el
retriever en memoria puntúa por solapamiento de tokens. Ninguno tiene
propiedades semánticas.

**Impacto.** Alto si se malinterpreta. Sirven para verificar filtros, orden,
citaciones e idempotencia; **no** para recall@5 ni citation precision.

**Acción tomada.** Advertencia explícita en el docstring del módulo, en
`rag/README.md` y en el [ADR 0004](../adr/0004-rag-hibrido-con-repositorio-inyectable.md).
El baseline de calidad exige el retriever real (F1.3).

### TD-03 — La detección de PII y secretos es sintáctica

**Descripción.** `reject_unsafe_keys` compara nombres de clave contra patrones.
No detecta un secreto guardado bajo un nombre inocuo ni PII incrustada en un
valor de texto libre.

**Impacto.** Medio. Es una barrera útil contra el descuido, no una garantía.

**Acción recomendada.** Complementar en F5.2 (`DIE-F5-011`) con una revisión de
valores, no solo de claves, sobre logs, eventos, datasets y reportes.

### TD-04 — La validación de propiedades A2UI está incompleta hasta Fase 1

**Descripción.** `A2UIComponent` absorbe cualquier propiedad desconocida en
`properties`, porque qué propiedades admite cada componente lo define el
catálogo, no el modelo. Una propiedad mal escrita se acepta hoy.

**Impacto.** Medio. `DIE-F1-102` exige prohibir propiedades desconocidas; el
contrato solo puede cumplirlo a medias.

**Acción recomendada.** El validador de catálogo de F1.13 (`DIE-F1-104`) debe
cerrar la allowlist por componente. Documentado y cubierto por
`test_a2ui_component_absorbs_unknown_properties_by_design`.

### TD-05 — Los contratos del MCP Mapper están congelados sin implementación

**Descripción.** §5.4 exige congelar `IntegrationDraft`, `MapperValidation`,
`ControlledTestResult`, `Approval` y `PublishedToolVersion` en Fase 0, pero el
Mapper es Fase 3. Se especificaron sin haber ejercitado el ciclo real.

**Impacto.** Bajo-medio. Es probable que F3.2 necesite campos adicionales;
serían cambios aditivos, compatibles con `v1`.

**Acción recomendada.** Revisar estos cinco contratos al inicio de Fase 3 antes
de construir el Mapper sobre ellos.

### TD-06 — LangGraph emite un `PendingDeprecationWarning` al importar

**Descripción.** `langgraph.checkpoint.serde.jsonplus` avisa sobre el valor por
defecto de `allowed_objects`. No depende de nuestro código.

**Impacto.** Bajo. La suite corre con `filterwarnings = ["error", ...]`, así que
hay dos supresiones puntuales en `pyproject.toml`.

**Acción recomendada.** Retirar las supresiones al actualizar LangGraph.

---

## 5. Mejoras detectadas fuera de alcance

Ninguna se implementó. Se registran para que se decidan en su fase.

| # | Mejora | Dónde | Fase sugerida |
|---|---|---|---|
| M-01 | El repositorio no tenía `.gitignore`; sin él, `.venv/` y `__pycache__/` acabarían versionados | Raíz | **Hecho** — era prerrequisito para trabajar |
| M-02 | `RunMetrics` no captura `first_event_ms` automáticamente; el gate de rendimiento exige «primer evento ≤ 2 s» | `contracts/.../execution.py` | F1.11, al instrumentar el grafo completo |
| M-03 | El `EventEmitter` podría derivar `actor_type` del `EventType` en vez de recibirlo, evitando combinaciones incoherentes | `orchestration/.../events.py` | F2.8, junto al event mapping para Cris |
| M-04 | `merge_run_state` toma los escalares del update; con fan-out real (F4.1) hará falta una regla explícita por campo | `orchestration/.../reducers.py` | F4.1 |
| M-05 | Los JSON Schema no se publican como OpenAPI; Dani los necesitará unificados para generar el cliente TypeScript | `contracts/openapi/` | Prerrequisito de Fase 1 |
| M-06 | No hay CI que ejecute `pytest` ni verifique el drift de artefactos generados | `.github/workflows/` | Antes de Fase 1 (Dani) |
| M-07 | `Money` no soporta resta ni comparación; el estimador las necesitará | `contracts/.../primitives.py` | F1.7 |
| M-08 | El detector de prompt injection tiene cuatro patrones en español; el corpus adversarial de F2.9 necesitará bastantes más | `rag/.../testing/retriever.py` | F2.9 |
| M-09 | `mypy` está configurado en `pyproject.toml` pero no se ejecutó en Fase 0 | Raíz | Antes de Fase 1, junto con CI |

---

## 6. Requiere decisión antes de Fase 1

| # | Pregunta | Dueño | Por qué bloquea |
|---|---|---|---|
| Q-01 | ¿Se ratifica `contracts/src/nexo_contracts/` como hogar del paquete Pydantic? | **Dani** | Es su carpeta. Si se mueve, cambian los imports de todos los módulos |
| Q-02 | ¿El schema físico de `run_events` y checkpoints admite `RunState` completo serializado? | **Daher** | Si exige normalizar el estado en tablas, cambia la política de checkpoints |
| Q-03 | ¿La API expone `RunResult` tal cual o con una envoltura propia? | **Dani** | Determina si `RunResult` es contrato de wire o solo interno |
| Q-04 | **Resuelta 2026-07-30:** se congela el `CatalogDescriptor` y JSONL implementados en el repo; no se migra al catálogo alternativo de la skill | **Tú / Cris** | El renderer se considera cerrado y Diego conecta esta frontera al flujo |
| Q-05 | ¿Se adopta `uv` con lockfile antes de CI? | **Dani** | Sin lockfile, CI no reproduce el árbol de dependencias |
| Q-06 | ¿Los nombres de evento de §5.8 son definitivos para el workflow viewer? | **Cris** | Renombrar un evento después de Fase 1 es un cambio incompatible |
| Q-07 | ¿Confirmas la corrección de la redacción de `DIE-F0-038` en el plan? | **Tú** | Ver H-03; hoy el plan se contradice consigo mismo |

---

## Anexo — cobertura de las tareas de Fase 0

| Paquete | Tareas | Estado |
|---|---|---|
| F0.1 decisiones y convenciones | `DIE-F0-001`…`010` | Completo — 5 ADR, matriz de propiedad, convenciones y glosario |
| F0.2 schemas y ejemplos | `DIE-F0-011`…`020` | Completo — 56 contratos, 149 artefactos, changelog |
| F0.3 puertos y dobles | `DIE-F0-021`…`030` | Completo — 10 puertos, 11 dobles, tabla de sustitución |
| F0.4 configuración segura | `DIE-F0-031`…`037` | Completo — 5 archivos, defaults que niegan, fail-fast |
| F0.5 grafo mínimo y eventos | `DIE-F0-038`…`044` | Completo — grafo, reducers, eventos, checkpoints, reanudación |
| §7.8 pruebas | 8 familias | Completo — 490 pruebas, sin red ni DB |
| §7.9 gate de salida | 6 criterios | 5 verificados; el 6.º (aceptación por consumidores) depende de §6 |
