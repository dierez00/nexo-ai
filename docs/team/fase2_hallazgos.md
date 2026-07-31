# Hallazgos de implementación — Fase 2

Fecha de corte: 2026-07-30.

Este documento registra decisiones, inconsistencias y deuda detectadas al
implementar exclusivamente la Fase 2. Las fuentes y adapters de esta fase son
sintéticos; no representan integraciones institucionales reales.

## H2-01 — No existía una fuente central de catálogo Core

**Descripción.** Los dominios, fuentes, tools, skills, modelos, políticas,
agentes y componentes A2UI estaban repartidos entre manifests sin una
proyección central que validara sus relaciones antes de delegar.

**Ubicación.** `agents/src/nexo_agents/catalog.py:27`,
`agents/src/nexo_agents/catalog.py:72`, `agents/src/nexo_agents/catalog.py:175`.

**Impacto.** Una referencia huérfana o una versión incompatible podía
descubrirse tarde y cada consumidor podía construir una vista distinta.

**Acción tomada.** Se creó un catálogo tipado con lifecycle cerrado,
validación de referencias, resolución de capabilities y export reproducible
para backend de agentes y web.

## H2-02 — El catálogo administrativo de Cris mostraba entidades ficticias

**Descripción.** La pantalla incluía agentes por dominio, versiones, salud y
volúmenes de uso hardcodeados que no existen en el runtime. El runtime usa
agentes transversales y parametriza `domain_navigator` por catálogo.

**Ubicación.** `apps/web/src/app/admin/catalogo/page.tsx:2`,
`apps/web/src/app/admin/catalogo/page.tsx:25`,
`apps/web/src/app/admin/catalogo/page.tsx:56`.

**Impacto.** La UI afirmaba capacidades y telemetría inexistentes, y podía
inducir a diseñar una topología de agentes distinta a la real.

**Acción tomada.** Se sustituyó el inventario manual por el snapshot generado
`apps/web/public/fixtures/catalog/core.json`; ahora distingue dominios,
agentes transversales, tools y skills. Se retiraron salud y uso inventados.

## H2-03 — El workflow web era una maqueta sin relación con `RunEvent`

**Descripción.** El grafo y la línea de tiempo de administración estaban
hardcodeados y no podían demostrar replay, secuencia ni correlación.

**Ubicación.** `apps/web/src/app/admin/workflow/page.tsx:2`,
`apps/web/src/features/workflow/WorkflowReplayView.tsx:87`,
`docs/team/workflow_event_mapping_v1.md:14`.

**Impacto.** No cubría `DIE-F2-056`–`DIE-F2-062` y podía divergir del workflow
real sin que una prueba lo detectara.

**Acción tomada.** Se definió un mapping estable, se generaron los cinco
replays requeridos y la vista consume la proyección de `success.json`. Una
prueba reconstruye cada fixture desde los eventos crudos y exige paridad con
la proyección almacenada.

## H2-04 — Dos skills referenciaban componentes fuera de `citizen:v1`

**Descripción.** Las skills MVP usaban `SourceCitation` y
`ConfirmationSummary`, pero el catálogo congelado publica `SourceList` y
`ConfirmButton`.

**Ubicación.** `domains/vehiculos/skills/skill_veh_renovacion.yaml:116`,
`domains/ayuntamiento_empresas/skills/skill_emp_apertura.yaml:117`,
`a2ui/src/nexo_a2ui/catalog.py:98`.

**Impacto.** Al activar validación A2UI de skills, el catálogo Core no podía
cargarse sin romper la frontera congelada.

**Acción tomada.** Se corrigieron únicamente las referencias de las skills al
vocabulario ya publicado. No se modificaron el catálogo ni los fixtures
congelados de `citizen:v1`.

## H2-05 — Los cinco namespaces no cubrían todo el lifecycle documental

**Descripción.** Algunos dominios carecían de fuente vencida o sustituida, y
Ayuntamiento tampoco tenía un caso documental adversarial activo.

**Ubicación.** `domains/ayuntamiento_empresas/sources.yaml:117`,
`domains/vehiculos/sources.yaml:132`,
`domains/registro_civil/sources.yaml:43`,
`domains/salud/sources.yaml:43`,
`domains/ganaderia/sources.yaml:43`.

**Impacto.** `DIE-F2-018` quedaba incompleto y no se podía probar el mismo
filtro de vigencia/inyección en los cinco dominios.

**Acción tomada.** Se agregaron fuentes sintéticas activas, vencidas,
sustituidas y adversariales donde faltaban, se recalcularon checksums y se
añadió una prueba matricial en `rag/tests/test_core_snapshot.py:65`.

## H2-06 — Texto hostil de una tool podía convertirse en un fact

**Descripción.** La proyección de respuestas MCP copiaba listas de texto al
contexto verificable sin descartar instrucciones hostiles.

**Ubicación.** `agents/src/nexo_agents/tool_facts.py:27`,
`agents/src/nexo_agents/tool_facts.py:175`,
`agents/src/nexo_agents/tool_facts.py:198`.

**Impacto.** Aunque una tool no amplía el allowlist, su payload podía contaminar
la respuesta como si fuera un dato administrativo.

**Acción tomada.** Se filtran señales estables de prompt injection antes de
crear facts y se agregó cobertura adversarial para tool responses.

## H2-07 — La acción pendiente del grafo estaba acoplada a dos dominios

**Descripción.** La construcción de writes reconocía explícitamente Vehículos
y, para cualquier otro dominio, asumía el flujo de Ayuntamiento.

**Ubicación.** `orchestration/src/nexo_orchestration/graph/mvp.py:795`,
`orchestration/src/nexo_orchestration/graph/mvp.py:947`.

**Impacto.** Registro Civil y Ganadería podían proponer una tool correcta en
el plan pero preparar parámetros o semántica de otra acción.

**Acción tomada.** La acción se resuelve desde el intent/catalog y se generan
parámetros mock explícitos por write registrado, preservando confirmación e
idempotencia en el executor.

## H2-08 — El backend mantiene un contrato local de eventos incompatible

**Descripción.** `backend` define otro `RunEvent` con `node_name` y `data`, sin
`visibility`, `public_data`, `correlation_id`, `parent_event_id`, catálogo ni
skill. Además, al persistir reduce el evento a tres campos.

**Ubicación.** `backend/src/nexo_api/schemas/run.py:32`,
`backend/src/nexo_api/services/runs/service.py:70`,
`backend/src/nexo_api/services/runs/service.py:160`.

**Impacto.** Un stream SSE real no puede conservar todavía la jerarquía ni la
separación público/restringido requerida por el replay Core.

**Acción recomendada.** No se cambió porque es frontera de Dani y hacerlo aquí
ampliaría el alcance. Antes de Fase 3 se debe decidir si backend importa
`nexo_contracts.RunEvent` directamente o mantiene un adapter versionado con
paridad demostrable.

## H2-09 — Persistencia e índices del corpus siguen en una frontera externa

**Descripción.** El snapshot, lineage, diff, smoke e idempotencia funcionan con
el repositorio determinista en memoria. `DIE-F2-024` exige coordinación con la
persistencia, aislamiento e índices de Daher.

**Ubicación.** `rag/src/nexo_rag/corpus/snapshot.py:30`,
`rag/src/nexo_rag/corpus/snapshot.py:47`,
`docs/team/diego_plan_implementacion_hasta_extremo.md:612`.

**Impacto.** El gate offline es reproducible, pero aún no demuestra el mismo
snapshot sobre PostgreSQL/pgvector ni aislamiento multi-tenant persistido.

**Acción recomendada.** Conservar el snapshot generado como oracle y acordar
con Daher una prueba de paridad del adapter persistente antes de Fase 3.

## H2-10 — La configuración E2E local perdía soporte async y markers

**Descripción.** `tests/pytest.ini` toma precedencia dentro de `tests/` y no
declaraba `asyncio_mode` ni el marker `security`.

**Ubicación.** `tests/pytest.ini:1`.

**Impacto.** Los E2E async no se ejecutaban correctamente desde esa raíz y las
pruebas adversariales producían warnings de marker desconocido.

**Acción tomada.** Se alineó la configuración local con las convenciones del
repo: `asyncio_mode = auto` y marker `security`.

## H2-11 — La colección global requiere `psycopg` no declarado

**Descripción.** `pytest --collect-only` falla al importar la suite de base de
datos porque `psycopg` no está instalado ni aparece como dependencia del
workspace.

**Ubicación.** `tests/integration/database/conftest.py:11`,
`pyproject.toml:37`.

**Impacto.** No se puede usar el comando global de pytest en un sync estándar,
aunque la suite Core aislada sí está verde.

**Acción recomendada.** No se agregó una dependencia de integración fuera de
alcance. Daher/Dani deben decidir si `psycopg` pertenece a un grupo opcional o
si la colección debe omitir esa suite cuando el extra no está instalado.

## H2-12 — `npm audit` reporta tres vulnerabilidades altas de producción

**Descripción.** El audit detecta advisories en `postcss` y `sharp`, transitivos
de Next. La solución automática propuesta usa `--force` y resolvería a
`next@9.3.3`, un cambio incompatible e inválido para este stack.

**Ubicación.** `apps/web/package.json:22`,
`apps/web/package-lock.json:6182`,
`apps/web/package-lock.json:7030`.

**Impacto.** Hay riesgo de XSS/divulgación en PostCSS y vulnerabilidades
heredadas de libvips en Sharp. No es seguro ignorarlo ni aplicar el downgrade
forzado sin estrategia.

**Acción recomendada.** No se ejecutó `npm audit fix --force`. Antes de Fase 3
se debe aprobar una versión corregida compatible de Next/dependencias o una
mitigación temporal documentada.

## H2-13 — Recharts 2 está deprecado

**Descripción.** La instalación advierte que Recharts 2 dejó de recibir
actualizaciones; el proyecto fija `^2.15.4`.

**Ubicación.** `apps/web/package.json:25`.

**Impacto.** Fase 3 añade superficies administrativas y puede profundizar la
dependencia justo antes de una migración mayor.

**Acción recomendada.** Cris debe decidir si migrar a Recharts 3 antes de
ampliar dashboards o congelar v2 con una ventana explícita de retiro.

## H2-14 — Orden ratificado: `retrieve` antes de `navigate`

**Descripción.** El plan heredado ubicaba navegación antes de retrieval. Se
ratifica el orden ejecutable: retrieval ocurre antes de navegar porque el
navigator necesita evidencia.

**Ubicación.** `orchestration/src/nexo_orchestration/graph/mvp.py:194`.

**Impacto.** El mapping visual y la documentación quedan alineados con el
runtime.

**Acción tomada.** Se preservó el grafo funcional y se corrigió la documentación
para declarar `retrieve → navigate`.

## H2-15 — La salud y el volumen del catálogo no tienen fuente runtime

**Descripción.** No existe todavía un contrato Core que entregue health checks
o conteos de uso para cada entidad del catálogo.

**Ubicación.** `apps/web/src/app/admin/catalogo/page.tsx:56`,
`agents/src/nexo_agents/catalog.py:334`.

**Impacto.** Mostrar badges de degradación o uso sería inventar telemetría; no
mostrarlos limita temporalmente la vista operacional.

**Acción tomada o recomendada.** La vista muestra sólo lifecycle/versiones
reales. Si Fase 3 requiere salud y uso, se debe definir su fuente de
observabilidad y política de frescura antes de reintroducirlos.

## H2-16 — El baseline Core es offline y no un indicador de producción

**Descripción.** Las cinco observaciones oficiales están congeladas y el
evaluator es determinista. Los recorridos E2E ejercitan el runtime con fakes,
pero no hay providers, corpus institucional ni juez externo.

**Ubicación.** `evaluations/baselines/core_v1_observations.jsonl:1`,
`evaluations/src/nexo_evaluations/evaluator.py:32`,
`tests/e2e/test_core_domains.py:27`.

**Impacto.** El reporte 5/5 sirve para detectar regresiones entre commits, no
para afirmar calidad productiva ni exactitud institucional.

**Acción tomada.** El reporte conserva versiones de dataset, configuración,
catálogo, corpus y skills, y la documentación identifica todo el contenido como
sintético.

## H2-17 — La reconexión lógica está probada, no coordinada con SSE real

**Descripción.** La secuencia conocida puede releerse y reconstruirse desde un
offset, pero la integración con el stream persistido de Dani sigue pendiente
por la incompatibilidad descrita en H2-08.

**Ubicación.** `orchestration/tests/test_event_sink.py:76`,
`orchestration/tests/test_workflow_replay.py:95`,
`docs/team/diego_plan_implementacion_hasta_extremo.md:664`.

**Impacto.** `DIE-F2-062` está cubierto en el port/doble offline, no en el
backend desplegable.

**Acción recomendada.** Usar los cinco fixtures y la prueba de paridad como
contrato de aceptación cuando Dani conecte SSE.
