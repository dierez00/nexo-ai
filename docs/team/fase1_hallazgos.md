# Fase 1 — hallazgos, decisiones y deuda técnica

> **Autor:** Diego. **Fecha:** 2026-07-30.
> **Alcance:** implementación de la Fase 1 (§8) de
> [`diego_plan_implementacion_hasta_extremo.md`](./diego_plan_implementacion_hasta_extremo.md).
> Continúa [`fase0_hallazgos.md`](./fase0_hallazgos.md).
>
> Formato por hallazgo: descripción, ubicación, impacto y acción tomada o
> recomendada.

## Índice

- [1. Bugs encontrados y corregidos](#1-bugs-encontrados-y-corregidos)
- [2. Inconsistencias del estado heredado](#2-inconsistencias-del-estado-heredado)
- [3. Decisiones tomadas](#3-decisiones-tomadas)
- [4. Deuda técnica asumida](#4-deuda-técnica-asumida)
- [5. Mejoras detectadas fuera de alcance](#5-mejoras-detectadas-fuera-de-alcance)
- [6. Requiere decisión](#6-requiere-decisión)
- [7. Baselines medidos](#7-baselines-medidos)

---

## 1. Bugs encontrados y corregidos

### H1-01 — `fragment_id` derivado del ordinal invalidaba en silencio toda citación previa

**Descripción.** Los identificadores de fragmento se derivaban de
`(source_id, document_id, version, ordinal)`. Cualquier cambio de chunking
—insertar una sección, ajustar el tamaño mínimo de fragmento— renumera todo lo
que viene después y reasigna los `fragment_id`.

El fallo es peor que romper: **no rompe**. Las citaciones ya emitidas siguen
validando, siguen apuntando a un fragmento que existe, y ese fragmento ya no
dice lo que decía cuando se citó. Una respuesta auditada meses después mostraría
una fuente que no respalda su claim.

Se manifestó al ajustar `MIN_CHUNK_CHARS`: el dataset de retrieval quedó
apuntando a fragmentos inexistentes y el recall cayó de 0.867 a 0.267 sin que
nada del retriever hubiera cambiado.

**Ubicación.** `rag/src/nexo_rag/corpus/ids.py:44` (`fragment_id`).

**Impacto.** Alto y silencioso. Afecta a la trazabilidad, que es el gate central
del sistema: «100% de los claims críticos incluyen `source_id` y `fragment_id`
activos» no significa nada si el `fragment_id` puede cambiar de contenido.

**Acción tomada.** `fragment_id` deriva ahora del **encabezado** de la sección,
no de su posición, con un índice de ocurrencia para desempatar encabezados
repetidos. Editar una sección deja de tocar el identificador de las demás.
`chunk_id` conserva el ordinal a propósito: es la unidad indexada y sí debe
reflejar un reindexado. Cubierto por
`test_fragment_ids_survive_a_change_in_a_neighbouring_section`.

### H1-02 — El stemmer no unificaba singular y plural

**Descripción.** El recorte de sufijos convertía `trámites` en `tramit` y
`trámite` en `tramite`. Las dos formas de la misma palabra no coincidían nunca,
que es exactamente lo contrario de para lo que existe un stemmer. La causa es
una ambigüedad real del español: `trámites` y `oficiales` terminan igual y sus
singulares son `trámite` y `oficial`; ninguna regla local los distingue.

**Ubicación.** `rag/src/nexo_rag/retrieval/lexical.py:124` (`stem`).

**Impacto.** Medio-alto sobre el recall: el vocabulario administrativo alterna
constantemente entre singular y plural («requisitos» en la consulta,
«requisito» en el documento).

**Acción tomada.** Se ordenaron los tres pasos —plural → sufijo derivativo →
vocal final átona— y se añadió el recorte de la vocal final, que es lo que hace
converger ambas formas sin necesitar un diccionario. Detectado por la prueba
`test_singular_and_plural_reach_the_same_stem`, que se escribió antes de mirar
la implementación.

### H1-03 — Normalizar BM25 por el mejor resultado hacía inútil cualquier umbral

**Descripción.** Los puntajes léxicos se normalizaban dividiendo por el máximo
**obtenido en esa consulta**, así que el primer resultado valía `1.0` siempre,
incluso cuando la consulta no tenía nada que ver con el corpus. «Cómo registro
una marca ante el IMPI» devolvía un fragmento de apertura de negocios con
puntaje perfecto.

Con eso, ningún umbral puede distinguir «esto responde» de «esto es lo menos
malo que hay», que es justo la distinción que necesita `DIE-F1-027`.

**Ubicación.** `rag/src/nexo_rag/retrieval/lexical.py` (`normalized_scores`,
eliminada).

**Impacto.** Alto: las consultas fuera de alcance devolvían evidencia falsa y
la citation precision quedaba capada.

**Acción tomada.** La normalización es contra el **máximo alcanzable** de la
consulta (`Σ idf(t)·(k1+1)`), que es comparable entre consultas y entre commits.
Cubierto por `test_scores_are_comparable_across_queries`.

### H1-04 — El scorer daba por aprobado un caso fuera de alcance que devolvía resultados

**Descripción.** `CaseScore.passed` comprobaba fragmentos faltantes y fuentes
prohibidas, pero no la violación de `expect_empty`. Un caso fuera de alcance que
devolvía cinco fragmentos irrelevantes tenía cero de ambas cosas y se contaba
como aprobado, mientras hundía la precisión sin explicar por qué.

**Ubicación.** `rag/src/nexo_rag/evaluation.py:118` (`CaseScore.passed`).

**Impacto.** Medio. Un evaluador que aprueba lo que no debe erosiona la
confianza en todo el dataset.

**Acción tomada.** Se añadió `unexpected_results` como tercera condición y se
reporta con su propio mensaje en `render_report`.

### H1-05 — Los embeddings deterministas daban coseno ~0.8 entre textos sin relación

**Descripción.** `DeterministicEmbeddings` derivaba los componentes de bytes de
un hash, todos positivos, así que **cualquier** par de vectores tenía coseno
alto. Con el retriever híbrido eso no es ruido inofensivo: la mitad vectorial
pesa 0.6, no discrimina nada y ahoga la mitad léxica, que sí. El recall del
perfil offline caía a 0.333.

**Ubicación.** `rag/src/nexo_rag/testing/embeddings.py:39`.

**Impacto.** Alto sobre la utilidad de la suite offline: mediría un retriever
que ordena por azar y lo reportaría como comportamiento real.

**Acción tomada.** Dos cosas. Los vectores se centran en cero, de modo que el
coseno de textos no relacionados ronda 0. Y —más importante— el puerto de
embeddings declara ahora `is_semantic`, y `HybridRetriever` **degrada `hybrid` a
`lexical`** cuando es falso. Un doble sin semántica ya no puede fingir que
soporta búsqueda híbrida.

### H1-10 — El validador de skills buscaba los prompts en la carpeta equivocada

**Descripción.** `validate_skill` pasaba la raíz del repositorio como directorio
de prompts (`load_by_ref(ref, root=root)`), y la referencia
`nexo_agents/prompts/classifier.v1.md` es relativa al **paquete**. Resultado:
toda referencia de prompt se declaraba inexistente, y el error listaba como
«prompts disponibles» los tres Markdown de la raíz del repositorio.

**Ubicación.** `agents/src/nexo_agents/skills.py:169`.

**Impacto.** Medio: la validación fallaba siempre, y una validación que falla
siempre acaba desactivándose (mismo patrón que H-02 de Fase 0).

**Acción tomada.** `load_by_ref` resuelve contra `prompts/` por defecto y su
parámetro pasó de llamarse `root` a `directory`, que es lo que era. El nombre
engañoso fue la causa del error.

### H1-11 — El validador exigía que cada dominio declarase los nueve agentes

**Descripción.** La comprobación «los pasos de la skill delegan en agentes que
el dominio declara» no distinguía entre agentes **transversales** —clasificador,
verificador, estimador, transaccional, redactor— y agentes **propios del
dominio**. Toda skill quedaba inválida por delegar en el verificador.

**Ubicación.** `agents/src/nexo_agents/skills.py:162`.

**Impacto.** Bajo, pero habría obligado a repetir nueve líneas idénticas en cada
`domain.yaml`, que es exactamente el ruido que un manifiesto debe evitar.

**Acción tomada.** Se declaró `TRANSVERSAL_AGENTS` y un dominio solo declara los
suyos —hoy, el navegador—. Cubierto por
`test_transversal_agents_do_not_need_to_be_declared_per_domain`.

### H1-12 — El manifiesto de vehículos apuntaba a una skill que no existía

**Descripción.** La intención `consultar_adeudo` declaraba
`skill_id: skill_veh_adeudo` y esa skill no estaba escrita. El supervisor
habría delegado a un plan inexistente.

**Ubicación.** `domains/vehiculos/domain.yaml:52`.

**Impacto.** Medio. Lo detectó la comprobación de referencias huérfanas del
propio validador, que es para lo que se escribió.

**Acción tomada.** Se escribió `skill_veh_adeudo.yaml`. La consulta de adeudo
merece skill propia: es un trámite independiente, gratuito y sin cita, y
fusionarlo con la renovación obligaría a quien solo quiere su saldo a recorrer
un plan de siete pasos.

### H1-13 — `opaque_id()` invalidaba la comprobación de tipos de los 24 identificadores

**Descripción.** Los IDs se generaban con una fábrica: `UserId = opaque_id("usr")`.
Una función devuelve un **valor**, no un tipo, así que para el analizador
estático `UserId` era `object` y cualquier uso como anotación producía
«Variable is not valid as a type». Eso desactivaba la comprobación de tipos de
los ~24 identificadores del sistema, que son justamente los campos que más
cruzan fronteras entre módulos.

Solo se vio al ejecutar `mypy` por primera vez (TD-05 de Fase 0, abierto desde
entonces): 112 errores, de los que ~40 salían de aquí y otros tantos eran
consecuencia.

**Ubicación.** `contracts/src/nexo_contracts/ids.py:72`.

**Impacto.** Alto y silencioso: el proyecto declara `strict = true` y en la
práctica no comprobaba nada sobre los IDs.

**Acción tomada.** Los 24 alias se escriben uno a uno como `Annotated[str, ...]`,
con las restricciones derivándose del prefijo en tiempo de ejecución. Los JSON
Schema publicados **no cambian** —se verificó con `git diff` tras regenerar—, así
que es un arreglo puramente estático.

### H1-14 — El plugin de mypy de Pydantic no estaba activado

**Descripción.** Sin `plugins = ["pydantic.mypy"]`, mypy no entiende
`default_factory` dentro de un `Annotated`, y reportaba como argumento
obligatorio cada campo con default. Era la otra mitad del ruido que hacía
inviable ejecutar el type checker.

**Ubicación.** `pyproject.toml`, sección `[tool.mypy]`.

**Acción tomada.** Plugin activado. Con eso y H1-13, los 112 errores bajaron a 8,
todos reales, y ahora `mypy --strict` pasa limpio sobre los seis paquetes.

### H1-15 — El grafo de Fase 0 pasaba un `str` donde se espera `ModelTaskKind`

**Descripción.** `minimal.py` invocaba el gateway con
`task_kind="classification"`. Funcionaba por coerción de Pydantic sobre un
`StrEnum`, pero la firma mentía y ningún type checker lo habría visto mientras
los IDs fueran `object`.

**Ubicación.** `orchestration/src/nexo_orchestration/graph/minimal.py:220`.

**Acción tomada.** Se pasa `ModelTaskKind.CLASSIFICATION`. Mismo caso en
`EventEmitter.emit`, cuyo `data` estaba tipado como `dict[str, object]` cuando
el contrato exige `JsonValue`.

### H1-16 — Un umbral no puede decidir a la vez «esto es evidencia» y «esto basta»

**Descripción.** El retriever usaba `MIN_FUSED_SCORE = 0.25` para dos cosas
incompatibles: recortar ruido y filtrar consultas fuera de alcance. Los datos lo
desmienten de forma tajante: sobre este corpus, la consulta **fuera de alcance**
«cómo tramito mi pasaporte» puntúa **0.308** y la consulta **legítima** «qué
permisos necesito para abrir una taquería» puntúa **0.280**.

Se solapan. Ningún umbral absoluto las separa, y subirlo solo descarta evidencia
buena —que es exactamente lo que estaba pasando: el fragmento correcto quedaba
fuera del top-5 porque el suelo lo cortaba antes.

**Ubicación.** `rag/src/nexo_rag/retrieval/hybrid.py:46`.

**Impacto.** Alto: era la causa de los dos casos que TD1-03 daba por
irresolubles.

**Acción tomada.** Separación de responsabilidades. El retriever **ordena** con
un suelo bajo orientado a recall (0.08); `retrieval.sufficiency.assess` decide si
lo recuperado sostiene un claim crítico. El dataset dejó de afirmar «no devuelve
nada» y pasa a afirmar «no basta» (`expect_insufficient`).

**Resultado:** perfil semántico **15/15, recall 1.000, precisión 1.000**; perfil
offline sube a 0.867/0.933 y **también cumple el gate**. El barrido de
`CONFIDENT_SCORE` entre 0.30 y 0.45 no cambia el resultado, lo que indica que la
separación la hace el diseño y no un número ajustado al dataset.

### H1-17 — El contrato hacía inexpresable el resultado de una escritura

**Descripción.** `VerifiedFact` exigía **citación documental activa** a todo
hecho crítico aceptado. Pero `ACTION_RESULT` está en
`CRITICAL_FACT_CATEGORIES` y por definición **nunca** procede de un documento:
su evidencia es la invocación de la tool y su folio.

El resultado es que el caso más importante del sistema —«la cita quedó
reservada, folio NEXO-MOCK-01»— **no se podía representar como hecho aceptado**.
Lo mismo con un adeudo consultado por tool: un `COST` verdadero, verificado
contra un resultado real, y el contrato lo rechazaba.

Salió al construir el verificador: el contrato falló al cerrar el snapshot.

**Ubicación.** `contracts/src/nexo_contracts/facts.py:186`
(`_critical_accepted_facts_need_active_citations`).

**Impacto.** Alto: bloqueaba `DIE-F1-054` y, con él, el cierre de los dos
recorridos oficiales.

**Acción tomada.** La invariante pasa a admitir **dos clases de evidencia**: una
citación activa o un `supporting_tool_call_id`. Es un cambio aditivo compatible
con `v1` (campo opcional nuevo + relajación de una restricción, §1 de
`conventions.md`). Lo que no cambia: sin ninguna de las dos, no hay aceptación.
Cubierto por `test_a_tool_call_is_the_other_admissible_evidence` y
`test_neither_kind_of_evidence_still_fails`.

### H1-18 — El estimador intentaba construir una estimación que el contrato prohíbe

**Descripción.** Ante costos en monedas distintas, el estimador devolvía
`total_cost=None` y seguía. Pero `Estimate` rechaza que los **pasos** mezclen
monedas, no solo el total, así que la construcción fallaba entera y el run se
quedaba sin ruta.

**Ubicación.** `agents/src/nexo_agents/estimator.py:191`.

**Impacto.** Medio. Es un caso raro hoy —todo el corpus está en MXN— y habría
sido un fallo duro el día que dejara de serlo.

**Acción tomada.** Se conserva la **ruta**, que sigue siendo correcta, y se
descarta el importe divergente con su aviso. Convertir en silencio era el único
desenlace inaceptable.

### H1-19 — La plantilla del redactor repetía el importe

**Descripción.** `_cost_line` añadía el monto formateado aunque el claim ya lo
dijera: «La renovación cuesta 814.00 MXN. — 814.00 MXN».

**Ubicación.** `agents/src/nexo_agents/writer.py` (`_cost_line`).

**Impacto.** Bajo, pero delata la plantilla. Y la plantilla es el camino de
respaldo: cuanto menos se note, mejor.

**Acción tomada.** El importe se añade solo si el claim no lo menciona ya.

### H1-20 — El schema de salida en modo serialización no era utilizable

**Descripción.** `ToolDefinition.output_schema()` generaba el JSON Schema con
`mode="serialization"`, y Pydantic devolvía un `{"$ref": ...}` en lugar de un
schema de objeto. La causa es el `model_serializer(mode="wrap")` de `NexoModel`,
que envuelve toda serialización.

**Ubicación.** `mcp/src/nexo_mcp/tools/definitions.py` (`output_schema`).

**Impacto.** Bajo hoy —el schema de salida es interno—, alto el día que se
publique junto al de entrada por `tools/list`.

**Acción tomada.** Se genera en modo validación. Conviene tenerlo presente para
cualquier otro artefacto que se derive de un `NexoModel` en serialización.

### H1-21 — Los parámetros de una tool no pueden ser objetos de Python

**Descripción.** `SafePayload` exige JSON puro, así que pasar un `date` como
parámetro de tool falla al construir el `ToolCall`. No es un bug: es la frontera
de proceso haciéndose notar. Lo registro porque **es fácil escribir el código
equivocado** —un `date` parece inofensivo— y el fallo aparece lejos, al
construir la invocación.

**Ubicación.** `contracts/src/nexo_contracts/safety.py`; se manifestó en
`mcp/tests/test_mcp_tools.py`.

**Acción tomada.** Prueba explícita `test_tool_parameters_must_be_pure_json`
para que el invariante quede escrito donde alguien lo busque.

### H1-22 — El `git pull` estaba bloqueado por trabajo local y un archivo no rastreado

**Descripción.** `origin/main` avanzó de `4131099` a `edfb473`, pero
`pyproject.toml` tenía cambios locales y `tests/__init__.py` existía sin
seguimiento justo en una ruta añadida por upstream. Un pull directo habría
sobrescrito ambos.

**Ubicación.** `pyproject.toml:1`; `tests/__init__.py:1`; estado Git previo a
`edfb473`.

**Impacto.** Alto para la integración: impedía incorporar los cambios de
Dani/Daher y cualquier borrado manual podía perder trabajo.

**Acción tomada.** Se respaldó el archivo no rastreado, se creó el stash
`codex-phase1-before-origin-edfb473`, se hizo fast-forward exacto a `edfb473` y
se reaplicó el trabajo local sin conflictos. El stash se conserva como punto de
recuperación; el respaldo era idéntico al archivo de upstream.

### H1-23 — El navegador buscaba solo el título corto de la intención

**Descripción.** La consulta RAG se construía con títulos como «Abrir negocio»
y descartaba la descripción del manifiesto. Ese texto no contiene «uso de
suelo», «protección civil», «aviso sanitario» ni otros términos que sí pide el
recorrido oficial de empresas, por lo que cuatro pruebas E2E no recuperaban
evidencia suficiente.

**Ubicación.** `agents/src/nexo_agents/navigator.py:393`;
`domains/ayuntamiento_empresas/domain.yaml:12`.

**Impacto.** Alto: `CAP-EMP-01` fallaba antes de navegar aunque el corpus
correcto sí estaba indexado.

**Acción tomada.** `query_for` incorpora título y descripción de cada intención,
y la descripción de `abrir_negocio` enumera explícitamente sus subtrámites.
Esto se resolvió investigando el corpus y el manifiesto, sin añadir heurísticas
especiales al retriever.

### H1-24 — El checkpoint dependía de memoria del proceso

**Descripción.** Clasificación, evidencia, tools propuestas y resultados de
lectura vivían en atributos temporales del grafo o en un `GraphState` que no
formaba parte del `RunState` persistido. Reanudar con una instancia nueva podía
omitir retrieval o verificar sin sus entradas.

**Ubicación.** `contracts/src/nexo_contracts/execution.py:304`;
`orchestration/src/nexo_orchestration/graph/mvp.py:483`.

**Impacto.** Crítico para `DIE-F1-086`–`088`: un checkpoint que solo funciona
con el mismo objeto Python no es reanudable.

**Acción tomada.** Los cuatro valores son ahora campos internos serializables
de `RunState`; se eliminó el estado mutable del grafo y del navegador. La prueba
`tests/e2e/test_cap_veh_01.py:267` restaura un checkpoint posterior a retrieval
en un grafo nuevo y comprueba que retrieval no se repite.

### H1-25 — Las contradicciones se detectaban después de cerrar el snapshot

**Descripción.** El verificador creaba `VerifiedFacts` y después el grafo
llamaba `detect_tool_document_conflicts`; el resultado se acumulaba en el
objeto verificador, pero el snapshot ya era inmutable y nunca recibía las
contradicciones. Además, comparar cualquier par de la misma categoría marcaba
como contradictorios el costo de renovación y un adeudo, aunque hablan de
conceptos distintos.

**Ubicación.** `agents/src/nexo_agents/verifier.py:108`;
`orchestration/src/nexo_orchestration/graph/mvp.py:628`.

**Impacto.** Alto: una contradicción real no bloqueaba escrituras y una
comparación ingenua podía bloquearlas por un falso positivo.

**Acción tomada.** La detección ocurre dentro de `verify`, antes de cerrar el
snapshot, con IDs únicos y exigencia de coincidencia temática entre claims. El
estado puntual de adeudo se proyecta como `context`, no como la regla normativa
`dependency`.

### H1-26 — Las tools de lectura no alimentaban la respuesta

**Descripción.** El grafo ejecutaba tools pero no convertía sus resultados en
hechos verificables; además, el navegador eliminaba sus parámetros y
`read_tools` forzaba `mode=read`, incluso para una tool `compute`. Se podía
afirmar que se consultaron adeudo, costos o citas, pero sus datos no llegaban al
verificador, estimador ni A2UI.

**Ubicación.** `agents/src/nexo_agents/tool_facts.py:1`;
`orchestration/src/nexo_orchestration/graph/mvp.py:534`.

**Impacto.** Alto: los recorridos oficiales eran nominales, no de extremo a
extremo.

**Acción tomada.** Se añadió una proyección cerrada para las siete tools de
lectura/cómputo del MVP, conservando `tool_call_id`; se preservan parámetros y
el modo real del catálogo. El estimador de vehículos separa el costo de renovar
del adeudo, y la acción confirmable reutiliza el vehículo y el primer slot
realmente consultados.

### H1-27 — Cancelar una acción pendiente era inválido para el propio contrato

**Descripción.** `ActionRequest` exigía consentimiento e idempotency key para
cualquier estado distinto de `pending_confirmation`, incluido `cancelled`.
Cancelar antes de escribir no debe equivaler a autorizar la escritura.

**Ubicación.** `contracts/src/nexo_contracts/execution.py:218`;
`orchestration/src/nexo_orchestration/graph/mvp.py:970`.

**Impacto.** Medio-alto: `DIE-F1-091` enumeraba `cancelled`, pero no había forma
válida de persistirlo.

**Acción tomada.** `cancelled` queda exento de las precondiciones de ejecución;
`MVPGraph.cancel` emite `run.cancelled`, persiste el estado y retira la acción de
`RunResult.available_actions`. Reanudar con confirmación después de cancelar no
ejecuta ninguna tool.

### H1-28 — El validador A2UI no comprobaba que los bindings existieran

**Descripción.** El contrato validaba hijos del árbol, pero una propiedad podía
referenciar `{"path": "/missing/title"}` y pasar el validator. Los manifiestos
de dominio también nombraban `SourceCitation` y `ConfirmationSummary`, mientras
el catálogo publicado contiene `SourceList` y `ConfirmButton`.

**Ubicación.** `a2ui/src/nexo_a2ui/validator.py:136`;
`domains/vehiculos/domain.yaml:88`;
`domains/ayuntamiento_empresas/domain.yaml:88`.

**Impacto.** Alto para el renderer: una superficie aceptada podía fallar al
resolver datos o pedir componentes inexistentes.

**Acción tomada.** El validador reconstruye el data model raíz y rechaza rutas
ausentes; los manifiestos se alinearon al catálogo y una prueba de coherencia
impide reincidir. Se entregaron dos fixtures JSONL válidos y tres inválidos en
`a2ui/fixtures/citizen/v1/`, cubiertos por contract tests.

### H1-29 — La orientación deducida se etiquetaba como catálogo

**Descripción.** Los hechos no críticos sin citación sobrevivían correctamente,
pero se guardaban con `origin=catalog` y sin el bloque `Deduction`, aunque eran
inferencias del navegador. Eso ocultaba fuente, confirmación y elegibilidad de
escritura exigidas por `DIE-F1-043`.

**Ubicación.** `agents/src/nexo_agents/navigator.py:326`.

**Impacto.** Medio: una orientación inferida parecía un dato canónico del
catálogo y perdía su trazabilidad.

**Acción tomada.** Se registra como `origin=deduction` con valor, fuente,
confianza, justificación, `confirmed_by_user=false` y
`write_eligible=false`. Los claims críticos sin evidencia continúan
descartándose.

### H1-30 — Citizen v1 quedó congelado como frontera del flujo

**Descripción.** Cris cerró su trabajo sobre A2UI y no habrá otra iteración del
formato antes de conectarlo. Mantener `citizen:v1` como propuesta editable
permitiría que catálogo, schemas o fixtures cambiasen silenciosamente mientras
el renderer ya depende de ellos.

**Ubicación.** `a2ui/catalogs/citizen/v1/freeze.json:1`;
`docs/adr/0006-a2ui-091-catalogo-cerrado-y-fallback.md:1`.

**Impacto.** Alto para la integración: el transporte necesita una frontera
estable y verificable, no solo una convención escrita.

**Acción tomada.** Se congelaron el descriptor, siete schemas y cinco fixtures
mediante SHA-256. `verify_frozen_catalog` detecta drift y `export_catalog`
rechaza sobrescribir v1 con contenido distinto. Cualquier evolución funcional
publica `urn:nexo-ia:a2ui:catalog:citizen:v2`.

---

## 2. Inconsistencias del estado heredado

### H1-06 — Los paquetes de Fase 0 no estaban en el workspace ni en la suite

**Descripción.** El `pyproject.toml` raíz no incluía `contracts`,
`orchestration`, `rag` ni `mcp` en `[tool.uv.workspace]`, ni en `testpaths`, ni
registraba los markers `e2e`/`contract`/`security`/`unit`, ni tenía los
`filterwarnings` ni los ignores de Ruff que `fase0_hallazgos.md` (D-13, TD-06)
afirma que tiene. `pytest` desde la raíz **no ejecutaba la suite de Fase 0**.

**Ubicación.** `pyproject.toml` contra `fase0_hallazgos.md` D-13 y TD-06.

**Impacto.** Alto: 490 pruebas existían y no corrían salvo que alguien pasara
las rutas a mano. En CI habrían sido invisibles.

**Acción tomada.** Se añadieron los seis paquetes al workspace y a `testpaths`,
más los markers, `filterwarnings` y `[tool.uv.sources]`. Nota: D-13 (`RUF001`-
`RUF003`) era innecesario —`RUF` no está en el `select` de Ruff—; se retiró la
afirmación aquí en vez de añadir configuración muerta.

### H1-07 — El lint del proyecto estaba rojo desde Fase 0

**Descripción.** `scripts/lint.sh` ejecuta `ruff check .` y `ruff format
--check .`, cuyo descubrimiento de archivos **no** depende del workspace de
`uv`. Los paquetes del núcleo llevaban desde Fase 0 con 15 errores de lint y 18
archivos sin formatear.

**Ubicación.** `scripts/lint.sh` contra `contracts/`, `orchestration/`, `rag/`,
`mcp/`.

**Impacto.** Medio. Un gate que nadie puede pasar deja de usarse.

**Acción tomada.** Se corrigió el origen en vez de silenciarlo: `known-first-party`
para que los imports del núcleo formen su propio bloque (que es como estaban
escritos), `allow-star-arg-any` para los passthrough `**kwargs`, y
`per-file-ignores` acotados a los tres módulos con hooks de Pydantic y a
`minimal.py` por la firma de LangGraph. Se ejecutó `ruff format` sobre los
paquetes del núcleo: es un reformateo mecánico, atribuible y de una sola vez.

Tras integrar `origin/main@edfb473`, `ruff check .` volvió a quedar rojo por
tres hallazgos nuevos dentro de las pruebas de base de datos de Daher; se
documentan en TD1-08 y no se modificaron fuera de su alcance.

### H1-08 — El catálogo A2UI ciudadano sigue sin existir

**Descripción.** `config/catalogs.yaml` apunta a
`a2ui/catalogs/citizen/v1/catalog.json`, que no existe. El PR #3 de Cris
(`feat(web): portal ciudadano…`) era íntegramente `apps/web` con fixtures
estáticos: no incluía renderer A2UI ni artefacto de catálogo, así que Q-04
estaba abierto durante la implementación inicial.

**Ubicación.** `config/catalogs.yaml:14` contra el árbol de `a2ui/`.

**Impacto.** Bloquea F1.13 hasta que se defina el formato.

**Acción tomada.** El catálogo ciudadano v1 se define en
`a2ui/src/nexo_a2ui/catalog.py` y el artefacto de `a2ui/catalogs/citizen/v1/`
se **genera** desde ahí, como los JSON Schema de `contracts`. La ruta que
declaraba `config/catalogs.yaml` ya existe, y una prueba lo verifica.
Posteriormente, la decisión H1-30 congeló ese formato y cerró Q-04.

### H1-09 — Los nombres de agente de la consola de Cris no existen en el contrato

**Descripción.** `apps/web/src/app/admin/catalogo/page.tsx` lista
`agente_vehiculos`, `agente_empresas`, `agente_registro_civil`… El enum
`AgentName` define `classifier`, `supervisor`, `domain_navigator`, `verifier`,
`estimator`, `transactional`, `writer`, `signal_analyst`, `judge` y
`prompt_assistant`. No hay un agente por dominio: hay **un** navegador de
dominio parametrizado por namespace.

**Ubicación.** `apps/web/src/app/admin/catalogo/page.tsx:25` contra
`contracts/src/nexo_contracts/enums.py:63`.

**Impacto.** Bajo hoy —son fixtures estáticos de maqueta—, alto cuando esa
pantalla se conecte al catálogo real: la agrupación por dominio no existe en los
datos.

**Acción recomendada.** Acordar con Cris antes de F2.1 si la consola muestra
agentes (del enum) o capacidades por dominio (del catálogo central). Son dos
entidades distintas.

---

## 3. Decisiones tomadas

| # | Decisión | Motivo | Dónde queda |
|---|---|---|---|
| D1-01 | SDK oficial `mcp` para el server | El wire shape real es lo que exige el ADR 0005 y `DIE-F1-072`; una imitación divergiría al conectar un cliente real | Lote 5 |
| D1-02 | Catálogo A2UI propio en formato `CatalogDescriptor`, con artefacto JSON generado para el renderer | Es la frontera implementada y congelada para `citizen:v1`; no se adopta el formato alternativo de la skill | Lote 6 |
| D1-03 | Embeddings reales con `model2vec` + `potion-multilingual-128M`; `sentence-transformers` queda disponible pero **no** por defecto | Se midió: el transformer no mejora el baseline (ver §7) | `rag/src/nexo_rag/embeddings.py` |
| D1-13 | Contrato `Classification` publicado en `contracts/` | Cierra H-08 de Fase 0; `FakeClassification` desaparece | `contracts/src/nexo_contracts/classification.py` |
| D1-14 | Las citaciones las construye el navegador, no el modelo | El modelo solo referencia fragmentos que se le mostraron; no puede inventar una fuente | `agents/src/nexo_agents/navigator.py` |
| D1-15 | Un hecho crítico sin evidencia se **descarta**, uno no crítico sobrevive sin citar | Orientar sin citar es legítimo; afirmar un requisito o un costo no | `navigator.py:_to_candidate_facts` |
| D1-16 | El fallback determinista del clasificador vive en `domain.yaml` (`keywords`) | Los casos oficiales deben clasificar sin proveedor; y las palabras clave son datos, no código | `domains/*/domain.yaml` |
| D1-17 | Agentes transversales no se declaran por dominio | Ver H1-11 | `agents/src/nexo_agents/skills.py` |
| D1-18 | El retriever ordena; `assess` juzga la suficiencia | Un umbral no puede hacer las dos cosas (ver H1-16) | `rag/.../retrieval/` |
| D1-19 | Las nueve tools del MVP quedan `enabled: true` | Ya tienen adapter, contratos, prueba y regla de permiso; la confirmación la sigue exigiendo `ToolMetadata` | `config/tool_registry.yaml` |
| D1-20 | La identidad viaja en `_nexo_context`, fuera de los parámetros | Un modelo que redacta parámetros no debe poder escribir su propio rol | `mcp/src/nexo_mcp/server.py` |
| D1-21 | Sin identidad de sesión, `tools/list` devuelve vacío | Revelar qué capacidades existen es el primer paso de un escalamiento | `mcp/src/nexo_mcp/server.py` |
| D1-22 | Los parámetros de tool son referencias opacas (`vehiculo_ref`, `predio_ref`) | `SafePayload` rechaza `placa` o `domicilio`: una tool que pidiera PII es inconstruible | `mcp/.../tools/definitions.py` |
| D1-04 | El adapter semántico **no** entra en el perfil offline | La primera carga descarga el modelo; la demo y la suite deben correr sin red | `rag/src/nexo_rag/embeddings.py` |
| D1-05 | Gateway de modelos en `orchestration/models/` | Es donde se declara `ChatModelPort` y donde se carga la configuración; los adapters de proveedor siguen siendo de Dani | `orchestration/src/nexo_orchestration/models/` |
| D1-06 | El costo lo calcula el gateway desde la configuración, no el adapter | Un solo lugar donde está escrito el precio de un modelo | `gateway.py:_cost` |
| D1-07 | Un alias habilitado sin adapter registrado detiene el arranque | Misma regla que `load_config`: fallar al inicio, no en el tercer nodo | `gateway.py:__post_init__` |
| D1-08 | El prompt nunca se registra; solo su forma | Un log es un destino de datos como cualquier otro | `models/redaction.py` |
| D1-09 | Dos umbrales de puntaje, léxico y fusionado | Las dos escalas no son comparables; uno solo o deja pasar consultas fuera de alcance o descarta evidencia legítima | `retrieval/hybrid.py` |
| D1-10 | Los checksums del corpus se generan con CLI, nunca a mano | Copiarlos a mano acaba en un manifest que dice una cosa y un archivo que dice otra | `rag/src/nexo_rag/corpus/cli.py` |
| D1-11 | El documento manipulado se declara `active` | El escenario a probar no es «un documento sospechoso queda fuera» sino «un documento legítimo fue alterado y sus órdenes no tienen efecto» | `domains/vehiculos/sources.yaml` |
| D1-12 | `nexo_agents` depende de `nexo_rag` y `nexo_mcp` | Solo por sus `Protocol`; importar un puerto no es importar una implementación | `agents/pyproject.toml` |
| D1-23 | El grafo ejecuta `retrieve` antes de `navigate` | El orden textual de `DIE-F1-083` pone `navigate` primero, pero el navegador necesita evidencia para construir hechos citables | `orchestration/.../graph/mvp.py` |
| D1-24 | Todo lo necesario para reanudar vive en `RunState`, no en atributos del grafo | Un checkpoint debe funcionar en otro proceso y otra instancia | `contracts/.../execution.py` |
| D1-25 | Los fixtures JSONL usan el protocolo v0.9.1 y el validator local; `CatalogDescriptor` es el formato definitivo de citizen v1 | Cris cerró A2UI y el siguiente trabajo es conectar esta frontera al flujo, no rediseñarla | `a2ui/catalogs/citizen/v1/freeze.json` |

---

## 4. Deuda técnica asumida

### TD1-01 — El modelo de embeddings pesa 507 MB, no los ~100 MB estimados

**Descripción.** `potion-multilingual-128M` ocupa 489 MB de pesos más 18 MB de
tokenizer. Autorizaste explícitamente usar `torch` si mejoraba la calidad, así
que se implementó también `TransformerEmbeddings`
(`intfloat/multilingual-e5-base`, con prefijos `query:`/`passage:`) y **se
midió**: no mejora (§7). El transformer alcanza exactamente el mismo
recall 0.867 / precisión 0.933 a cambio de ~2.5 GB de dependencias y ~1.1 GB de
modelo, así que no se adopta por defecto.

**Impacto.** Medio. No afecta a la suite ni a la demo, que usan el doble
determinista; sí al primer arranque de quien quiera medir el baseline real.

**Acción recomendada.** Revisar la comparación cuando el dataset crezca en F2.9:
con 15 casos, el techo lo pone el dataset, no el modelo. `TransformerEmbeddings`
queda en el código y probado para ese momento. Si el tamaño local molesta, la
otra salida es un adapter de proveedor remoto detrás del mismo
`EmbeddingsAdapterPort`, que ya existe.

### TD1-07 — A2UI citizen v1: cerrado

**Hecho.** Catálogo ciudadano v1 (10 componentes, 2 interactivos), builder desde
`VerifiedFacts`, validator contra el catálogo y fallback de canal con lista
numerada para WhatsApp. Los cuatro casos adversariales de §8.18 están cubiertos,
más esquemas de URL peligrosos y acciones de otro run. **Cierra `TD-04` de Fase
0**: la allowlist de propiedades por componente ya existe.

Los fixtures JSONL válidos e inválidos de `DIE-F1-109` ya están en
`a2ui/fixtures/citizen/v1/` y los valida la misma implementación que construye
las superficies.

El formato quedó ratificado y congelado por decisión del 2026-07-30. El auditor
de la skill `build-a2ui-frontend` espera otro formato de catálogo JSON Schema
con `$id`, `catalogId`, `components` y `functions`; no se usa para citizen v1.
La compatibilidad se verifica con los contratos y el validator del repo más las
huellas de `freeze.json`.

**Fuera todavía:** catálogo administrativo y formularios, ambos de Fase 3. No
son deuda del catálogo ciudadano congelado.

### TD1-02 — El baseline se mide sobre 15 casos y corpus sintético

**Descripción.** Los números de §7 salen de un dataset de 15 casos sobre un
corpus de 49 fragmentos escritos por mí. Cumplir el gate aquí **no** es cumplirlo
sobre corpus institucional real.

**Impacto.** Alto si se malinterpreta. Sirve como detector de regresión entre
commits, no como evidencia de calidad.

**Acción recomendada.** `capstone_v1` (F2.9, `DIE-F2-063`) debe ampliar el
dataset y, sobre todo, incluir casos que no haya escrito quien escribió el
corpus.

### TD1-03 — Dos casos del dataset fallaban con embeddings reales: cerrado

**Estado.** Resuelto por H1-16. No era calibración sino un error de diseño: un
solo umbral hacía dos trabajos incompatibles. Con el ranking y el juicio de
suficiencia separados, el perfil semántico pasa 15/15.

**Sigue en pie:** los dos casos que fallan en el perfil **offline** son
precisamente los que exigen semántica («permiso sanitario» ≟ «aviso de
funcionamiento sanitario»). Eso no es un defecto: es la diferencia que justifica
tener embeddings.

### TD1-04 — El chunking solo entiende Markdown

**Descripción.** `CHUNKERS` registra `text/markdown` y nada más. El corpus real
traerá PDF y HTML.

**Impacto.** Bajo hoy: un tipo no registrado se rechaza con motivo, no se ingiere
mal. Alto cuando llegue corpus institucional.

**Acción recomendada.** Añadir estrategias por tipo en F2.3 (`DIE-F2-017`),
conservando la regla de que los offsets apuntan al original.

### TD1-05 — `mypy` ya se ejecuta: cerrado

**Estado.** Resuelto. `mypy --strict` pasa limpio sobre los seis paquetes del
núcleo. Encontró tres bugs reales (H1-13, H1-14, H1-15) que llevaban ahí desde
Fase 0. M-09 queda cerrado.

**Compatibilidad con instalación base.** `Model2VecEmbeddings` y
`TransformerEmbeddings` conservan imports bajo `TYPE_CHECKING`, por lo que
`mypy` intentaba resolver `model2vec` y `sentence-transformers` incluso cuando
sus extras opcionales no estaban instalados. Esto hacía fallar la validación
después de un `uv sync --all-packages --frozen` limpio, aunque el código de
producción los carga de forma diferida y la suite base no los necesita.

**Ubicación.** `rag/src/nexo_rag/embeddings.py:32-33`;
`pyproject.toml`, overrides de `mypy`.

**Impacto.** Dos falsos positivos `import-not-found` en la validación base y la
tentación de instalar `sentence-transformers`/`torch` sin necesidad.

**Acción tomada.** Se ignoró exclusivamente la ausencia de esos dos módulos
opcionales y sus submódulos. El modo `strict` sigue activo para el código del
repositorio; los jobs que midan el backend semántico deben instalar su extra.

**Pendiente para Dani:** incluirlo en CI junto a `pytest` y `ruff`.

### TD1-06 — `backend/` e `integrations/` rompen la recolección de `pytest`

**Descripción.** Después de integrar `origin/main@edfb473`, sus pruebas fallan
al importar (`ModuleNotFoundError: fastapi`, `psycopg`,
`nexo_integrations`) porque el entorno virtual local no está sincronizado con
los paquetes que upstream añadió al workspace. `uv` tampoco está instalado en
esta máquina, por lo que no se pudo ejecutar `uv sync --all-packages --frozen`.
Es ajeno al alcance de Fase 1, pero significa que `pytest` a secas desde la raíz
no termina.

**Impacto.** Medio: el comando obvio no funciona.

**Acción recomendada.** Instalar `uv` y sincronizar el lockfile en el entorno de
desarrollo/CI. Mientras tanto, el núcleo se verifica pasando explícitamente sus
rutas y `-c pyproject.toml`; `tests/pytest.ini` usa otra configuración cuando
pytest elige el root desde `tests/`.

### TD1-08 — Las pruebas de base de datos integradas dejan rojo el lint global

**Descripción.** `ruff check .` reporta formato `%` obsoleto, un import no usado
y una línea de 101 caracteres en archivos añadidos por Daher.

**Ubicación.** `tests/integration/database/conftest.py:119`;
`tests/integration/database/test_backup_smoke.py:19`;
`tests/integration/database/test_backup_smoke.py:61`.

**Impacto.** Bajo sobre Fase 1, medio sobre CI: el lint acotado a los módulos de
Diego pasa, pero `scripts/lint.sh` examina todo el repo.

**Acción recomendada.** Daher debe aceptar el autofix equivalente en su código
o incorporar su versión corregida. No se tocó durante Fase 1 para respetar la
propiedad de sus cambios recién integrados.

### TD1-09 — El workflow de CI mezcla la suite offline con integración

**Descripción.** El workflow integrado desde `origin/main` instala
correctamente `uv 0.12.0`, pero `bash scripts/test.sh` ejecuta también las
pruebas `integration` de base de datos sin levantar Supabase.

**Ubicación.** `.github/workflows/ci.yml:29`.

**Impacto.** Alto para CI: puede fallar al intentar conectar a PostgreSQL,
independientemente de Fase 1.

**Acción recomendada.** En el job rápido, usar
`pytest -m "not integration"`. Ejecutar las pruebas de base de datos en un job
separado que levante Supabase y exporte `DATABASE_URL`. Por instrucción expresa,
no se modificó ni ejecutó el workflow en este turno.

**Corrección.** La afirmación inicial de que uv 0.12.0 no estaba publicado fue
incorrecta. El instalador oficial descargó esa versión y
`uv sync --all-packages --frozen` terminó correctamente el 2026-07-30.

---

## 5. Mejoras detectadas fuera de alcance

| # | Mejora | Dónde | Fase sugerida |
|---|---|---|---|
| M1-01 | El `BM25Index` se reconstruye en cada consulta; con corpus real hará falta índice persistente | `retrieval/lexical.py` | F2.3, junto a los índices de Daher |
| M1-02 | Los pesos de fusión son constantes; un reranking aprendido daría más | `retrieval/hybrid.py` | F4.3, con los mini-RAGs |
| M1-03 | `EmbeddingsGateway` no cachea vectores entre corridas; reingerir recalcula todo | `models/gateway.py` | F2.3 |
| M1-04 | La lista de stopwords es corta y fija; convendría derivarla del corpus | `retrieval/lexical.py` | F2.9 |
| M1-05 | `describe_request` no se emite todavía a ningún evento; el gateway solo lo expone | `models/redaction.py` | F3.8, observabilidad de agentes |
| M1-06 | CI ya existe, pero falta separar el job offline del job Supabase y añadir el baseline | `.github/workflows/ci.yml` | Antes de Fase 2 (Dani); ver TD1-09 |
| M1-08 | Unificar la configuración pytest raíz con `tests/pytest.ini` para que no dependa de la ruta invocada | `pyproject.toml:142`, `tests/pytest.ini:1` | Dani/Daher, antes de CI |

---

## 6. Requiere decisión

`Q1-05` quedó **resuelta el 2026-07-30**: citizen v1 conserva y congela el
`CatalogDescriptor`, schemas y JSONL del repositorio. No se migra al formato
alternativo de la skill; Diego conecta esta frontera al flujo.

| # | Pregunta | Dueño | Por qué importa |
|---|---|---|---|
| Q1-01 | ¿La consola de catálogo muestra agentes del enum o capacidades por dominio? | **Cris** | Ver H1-09; hoy la maqueta asume una entidad que no existe |
| Q1-02 | ¿Se acepta el peso de 507 MB del modelo de embeddings, o se prefiere un adapter remoto? | **Tú / Dani** | Ver TD1-01 |
| Q1-03 | ¿Los `fragment_id` derivados del encabezado se consideran estables para las citaciones que persistirá Daher? | **Daher** | Un cambio de encabezado sigue cambiando el ID; hay que decidir si eso exige migración |
| Q1-04 | Las preguntas Q-01…Q-07 de Fase 0 siguen abiertas | **Dani, Daher, Cris** | Fase 1 avanza asumiendo los contratos del repositorio como fuente de verdad |
| Q1-06 | ¿Se elimina `tests/pytest.ini` o se replica ahí la configuración raíz? | **Daher / Dani** | Hoy el resultado de pytest cambia según la ruta con que se invoque |

---

## 7. Baselines medidos

Medidos sobre `rag/datasets/retrieval_mvp.v1.json` (15 casos) y el corpus MVP
(49 fragmentos, 9 fuentes, 2 dominios). Reproducibles con
`python -m nexo_rag.baseline [--lexical|--semantic]`.

| Perfil | Embeddings | Peso | recall@5 | citation precision | Gate §3 |
|---|---|---:|---:|---:|---|
| Offline (suite y CI) | `fake-embeddings-v1`, degrada a léxico | 0 | 0.867 | 0.933 | Cumple métricas agregadas |
| Solo léxico (BM25) | — | 0 | 0.867 | 0.933 | Cumple métricas agregadas |
| **Semántico (por defecto)** | `model2vec:potion-multilingual-128M` | ~507 MB | **1.000** | **1.000** | **Cumple; 15/15 casos** |
| Transformer (disponible) | `sentence-transformers:multilingual-e5-base` | ~3.6 GB | 0.867 | 0.933 | Cumple |

Objetivos del gate: recall@5 ≥ 0.80 y citation precision ≥ 0.90.

**Sobre el transformer.** Se midió barriendo el umbral de fusión entre 0.25 y
0.65. Su mejor punto (0.55) empata exactamente con model2vec: mismos dos casos
fallidos, mismas métricas. No es que el transformer sea peor —es que con 15
casos el techo lo pone el dataset, no el modelo—, así que no hay motivo para
pagar 3 GB de dependencias. La comparación debe repetirse cuando `capstone_v1`
amplíe el dataset en F2.9.

**Cómo leer esta tabla.** El perfil offline y el léxico superan los dos
umbrales agregados, pero solo resuelven 13/15 casos sin faltantes estructurales:
fallan `emp-orden-de-tramites-taqueria` y
`emp-aviso-sanitario-alimentos`. El perfil semántico sí resuelve 15/15 y el
artefacto `rag/datasets/baseline_retrieval.json` conserva exactamente
recall/precision 1.000. La suite usa el perfil offline para no depender de red;
la evidencia del gate de calidad es el perfil semántico, con la salvedad de
TD1-02.
