# Inventario de adapters falsos (integraciones institucionales)

Fecha de corte: 2026-07-31.

Este documento responde a los puntos 1 y 2 del checklist de "Integraciones
institucionales": identifica todos los adapters/dobles falsos que existen hoy
en el repositorio y documenta qué comportamiento institucional simula cada
uno. Describe **estado actual**; no propone todavía el rediseño de interfaces
ni la sustitución por integraciones reales (puntos 3-10), que quedan fuera de
alcance de este documento.

## Resumen

Hoy no existe ningún adapter institucional "real": el gobierno de Durango no
ha otorgado acceso a ningún sistema. Todo el comportamiento institucional
(vehículos, ayuntamiento/empresas, registro civil, salud, ganadería) está
simulado. La simulación **no vive** en `integrations/src/nexo_integrations/`
—ese paquete solo contiene stubs vacíos— sino directamente dentro de las
tools de MCP (`mcp/src/nexo_mcp/tools/definitions.py`). Esta desviación
respecto al límite documentado en
`technical-architecture.md` y los contratos de `integrations/`.
("`integrations` adapta proveedores... `mcp` ejecuta capacidades") es la
brecha principal a resolver cuando se aborden los puntos 3 y 4 del checklist.

## 1. Adapters institucionales mock (los 21 "trámites" simulados)

Ubicación: [`mcp/src/nexo_mcp/tools/definitions.py`](../../mcp/src/nexo_mcp/tools/definitions.py).
Cada handler es una función pura `_verbo_objeto(payload) -> Output`, sin
efectos secundarios, registrada junto a su `ToolMetadata` (`is_mock=True`,
`timeout_ms=5000`, permisos y modo lectura/escritura).

| Dominio | Tool | Qué simula |
|---|---|---|
| `vehiculos` | `consultar_adeudo` | Consulta de adeudo vehicular. Si la referencia termina en `_sin_adeudo` devuelve $0; cualquier otra referencia devuelve un adeudo fijo de $480.00 MXN por "infracción por estacionamiento indebido" que bloquea la renovación. |
| `vehiculos` | `localizar_modulo` | Directorio de módulos de atención vehicular (Centro, Norte, Poniente) con horario y trámites que atiende cada uno; filtra por trámite solicitado. |
| `vehiculos` | `buscar_citas` | Disponibilidad de citas: genera 3 slots consecutivos a partir de una fecha fija de catálogo (`citas-2026-07-30`). |
| `vehiculos` | `reservar_cita` | Confirmación de una cita: devuelve un `cita_id` derivado del `slot_id` y una fecha fija (2026-08-03 09:00 UTC). |
| `ayuntamiento` | `consultar_uso_suelo` | Validación de uso de suelo para apertura de negocio: reglas deterministas sobre superficie (`<=60 m²`) y referencia de predio (zona H1 vs H3). |
| `ayuntamiento` | `calcular_costos` | Cálculo de costos de permisos municipales (línea por línea). |
| `ayuntamiento` | `consultar_requisitos_negocio` | Lista de requisitos documentales para abrir un negocio. |
| `ayuntamiento` | `consultar_citas` | Disponibilidad de citas municipales. |
| `ayuntamiento` | `registrar_solicitud` | Registro de una solicitud de apertura de empresa (folio simulado). |
| `registro_civil` | `clasificar_tipo_correccion` | Clasificación del tipo de corrección de acta (heurística fija, no LLM). |
| `registro_civil` | `localizar_oficialia` | Directorio de oficialías del registro civil. |
| `registro_civil` | `consultar_disponibilidad` | Disponibilidad de citas de registro civil. |
| `registro_civil` | `registrar_solicitud` | Registro de una solicitud de trámite civil (folio simulado). |
| `salud` | `localizar_unidad_salud` | Directorio de unidades de salud (Secretaría de Salud, DIF, municipales) que atienden un servicio, p. ej. salud mental. |
| `salud` | `consultar_servicios` | Catálogo de servicios que ofrece una unidad de salud. |
| `salud` | `consultar_requisitos` | Requisitos/documentos para ser atendido en una unidad de salud. |
| `salud` | `buscar_horarios` | Horarios de atención de una unidad de salud. |
| `ganaderia` | `consultar_animal` | Ficha de un animal por folio/arete. |
| `ganaderia` | `consultar_historial` | Historial sanitario de un animal. |
| `ganaderia` | `registrar_vacuna` | Registro de aplicación de una vacuna (escritura, folio simulado). |
| `ganaderia` | `validar_movilizacion` | Validación de requisitos para mover ganado entre predios/municipios. |
| `ganaderia` | `consultar_alertas` | Alertas sanitarias/ganaderas activas para un predio o región. |

Estado de resiliencia y trazabilidad de estas 21 tools (aplicado por la capa
que las invoca, `mcp/src/nexo_mcp/execution.py::ToolExecutor`, no por los
handlers mismos):

- **Timeout:** sí, `asyncio.wait_for(metadata.timeout_ms)` por invocación.
- **Reintentos:** sí, pero solo para lecturas (`ToolMode.READ`) y solo ante
  `TOOL_TIMEOUT`/`PROVIDER_ERROR`; nunca para escrituras
  (`max_attempts == 1` es invariante de contrato) ni ante `UNKNOWN_OUTCOME`.
- **Marca explícita de mock:** sí, a nivel de contrato — `ToolMetadata.is_mock`,
  `ToolResult.is_mock` y `ToolConfirmation.is_mock` son `bool` con default
  `True` (`contracts/src/nexo_contracts/tools.py`). Falta confirmar si esa
  marca se traduce en algo visible para el ciudadano en la respuesta final
  (redactor/A2UI) — no verificado en este documento.
- **Registro de solicitud/respuesta sin datos sensibles:** no implementado a
  nivel de adapter/tool; no se observó logging de request/response en
  `definitions.py` ni en `execution.py` más allá de los eventos de ejecución
  del grafo.
- **Fuente citada en la respuesta:** los `Output` de estas tools no incluyen
  un campo de fuente/referencia normativa; la trazabilidad de fuentes hoy es
  responsabilidad exclusiva del `RAG` (`SourceCitation`), no de las tools.

## 2. Otros dobles de prueba (no institucionales, pero relevantes al patrón)

| Fake | Ubicación | Qué simula | Interfaz que implementa |
|---|---|---|---|
| `FakeActionExecutor` | `backend/src/nexo_api/services/actions/fake.py` | Ejecutor transaccional: siempre devuelve éxito con folio sintético `FOLIO-xxxxxxxx`. | `ActionExecutor` (Protocol, `services/actions/port.py`) |
| `FakeOrchestrator` | `backend/src/nexo_api/services/orchestration/fake.py` | Orquestador completo: emite `RUN_STARTED`/`RUN_COMPLETED` y una respuesta canónica de demo; marca `warnings=["fake_orchestrator"]`. | `Orchestrator` (Protocol, `services/orchestration/port.py`) |
| `FakeChatModel` / `FakeChatAdapter` | `orchestration/src/nexo_orchestration/testing/fake_model.py` | Llamadas a LLM de chat, con comportamientos programables (`FakeBehavior`: éxito, salida inválida, timeout, rate limit, proveedor caído). | `ChatModelPort` / `ChatAdapterPort` |
| `FakeEmbeddingsAdapter` | mismo archivo | Generación de embeddings de un proveedor externo. | `EmbeddingsAdapterPort` |
| `DeterministicEmbeddings` | `rag/src/nexo_rag/testing/embeddings.py` | Embeddings no semánticos (hash determinista); degrada la búsqueda híbrida a solo léxica. | — |
| `InMemoryRetriever` / `InMemoryChunkRepository` | `rag/src/nexo_rag/testing/retriever.py` | Almacén vectorial/FTS en memoria, sustituto de PostgreSQL+pgvector. | `RetrieverPort` / `ChunkRepositoryPort` |
| `InMemoryToolExecutor` / `InMemoryToolRegistry` | `mcp/src/nexo_mcp/testing/executor.py`, `testing/registry.py` | Ejecutor/registro de tools programable por escenario (`ToolBehavior`: success, timeout, schema_error, permission_denied, unknown_outcome, not_found); marca `is_mock=True`, `provider="mock"`. | `ToolExecutorPort` / `ToolRegistryPort` |

Estos no simulan sistemas institucionales de Durango; simulan proveedores de
infraestructura (LLM, embeddings, almacén vectorial, orquestador, ejecutor
transaccional). Se listan porque comparten el mismo patrón de contrato
(`is_mock`, comportamiento programable) y porque el checklist de item 7 exige
timeouts/reintentos/logging consistentes en toda la capa de integraciones, no
solo en la institucional.

## 3. `integrations/src/nexo_integrations/` — estado real

`institutional/__init__.py`, `models/__init__.py` y `storage/__init__.py`
contienen **únicamente un docstring**, sin código. No hay ningún adapter
institucional implementado en este paquete hoy; toda la lógica descrita en
la sección 1 vive en `mcp/tools/definitions.py` en su lugar. El único
adapter real y funcional en `integrations` es `twilio/` (verificación de
firma, normalización de WhatsApp, hashing de PII) — no es un fake.

`config/tool_registry.yaml` lista `name/version/domain/mode/enabled` por
tool pero no distingue mock/real; esa distinción solo existe hoy en
`ToolMetadata.is_mock` a nivel de contrato.

## Brechas identificadas (para las fases donde se aborden los puntos 3-10)

- No existe una interfaz (`Protocol`/ABC) por adapter institucional dentro de
  `integrations`; la lógica mock está acoplada a la capa MCP en vez de
  detrás de un puerto sustituible.
- No hay logging de request/response para las tools institucionales.
- No está verificado que `is_mock` se muestre al usuario final en la
  respuesta redactada o en A2UI.
- Los `Output` de las tools institucionales no cargan una referencia de
  fuente normativa (a diferencia de `SourceCitation` en RAG).
- `config/tool_registry.yaml` no tiene un campo mock/real explícito.
