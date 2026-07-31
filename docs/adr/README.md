# Architecture Decision Records

## Objetivo

Registrar decisiones relevantes y sus consecuencias para evitar rediscutirlas sin contexto.

## Contenido permitido

Contexto, opciones, decisión, consecuencias, estado y enlaces.

## Fuera de alcance

Minutas generales, tareas y decisiones triviales/reversibles.

## Convenciones

`NNNN-titulo-kebab-case.md`; estados `proposed`, `accepted`, `superseded`, `rejected`; no editar consecuencias históricas, crear un ADR que sustituya.

Responsable: autor de la decisión; revisión del dueño afectado.

Dependencias permitidas: propuesta, arquitectura, contratos y evidencia técnica; el runtime nunca depende de ADR.

## Ejemplos, tareas y terminado

Ejemplo: `0001-monolito-modular.md`. Primeros ADR: monolito modular, LangGraph, PostgreSQL/pgvector, A2UI 0.9.1 y Twilio. Un ADR está terminado cuando cita evidencia, tradeoffs y criterio de reevaluación.

## ADR publicados

| ADR | Título | Estado | Dueño |
|---|---|---|---|
| 0001 | *Reservado: monolito modular* | pendiente | Equipo |
| [0002](./0002-grafo-langgraph-estado-y-checkpoints.md) | Grafo LangGraph, estado serializable y checkpoints | accepted | Diego |
| [0003](./0003-model-gateway-por-aliases.md) | Model gateway por aliases y adapters | accepted | Diego |
| [0004](./0004-rag-hibrido-con-repositorio-inyectable.md) | RAG híbrido con repositorio inyectable | accepted | Diego |
| [0005](./0005-mcp-frontera-de-capacidades.md) | MCP como frontera de capacidades | accepted | Diego |
| [0006](./0006-a2ui-091-catalogo-cerrado-y-fallback.md) | A2UI v0.9.1, catálogo cerrado y fallback | accepted | Diego |

`0001` queda reservado para el ADR de monolito modular y un número posterior
para el de Twilio, ambos fuera del alcance de Diego.
