# Orquestación

## Objetivo

Convertir una solicitud en un grafo observable, reanudable e idempotente mediante LangGraph.

## Debe contener

`RunState`, supervisor, nodes/edges, reducers, checkpoints, interrupts, router de modelos, timeouts y emisión de eventos.

## No debe contener

Presentación, SQL ad hoc ni SDKs específicos de Twilio/modelos.

## Convenciones

Estado serializable; nodos idempotentes; fan-out explícito; merge determinista; ninguna escritura antes del interrupt de confirmación.

## Dependencias y responsable

Depende de `contracts`, `agents` e interfaces RAG/MCP/observabilidad. Responsable: Diego.

## Ejemplos y tareas

`graph.py`, `state.py`, `nodes/verify.py`, `model_router.py`. Construir grafo secuencial MVP, eventos/checkpoints y paralelismo Extremo.

## Terminado

La traza reconstruye decisiones; reanudar no duplica efectos; las ramas paralelas consolidan igual sin importar el orden.

## Estado tras Fase 1

Implementado:

- `RunState` serializable y sus reducers deterministas (`reducers.py`).
- Puertos de ejecución en `ports/`: chat model, checkpoint store, event sink,
  clock e ID factory. Los de retrieval y tools viven en `rag` y `mcp`.
- Dobles en memoria en `testing/`, publicados como parte del paquete porque los
  consumen otros módulos y la demo offline.
- Grafo mínimo `start → classify_fake → finalize_fake` sobre LangGraph
  (`graph/minimal.py`), con eventos secuenciados, checkpoints y reanudación.
- Carga y validación fail-fast de `config/` (`configuration.py`).
- Gateway de modelos con routing, presupuesto, redacción de logs y fallback.
- Grafo MVP de doce nodos (`graph/mvp.py`), checkpoints autocontenidos,
  confirmación/reanudación, cancelación, budgets y eventos monotónicos.
- Resultados de tools de lectura persistidos y proyectados a hechos antes de
  verificar; una escritura confirmada no duplica efectos.

El fan-out real queda para Fase 4; Fase 1 mantiene verificación y estimación
secuenciales como exige el plan.

Este es el **único** módulo que importa LangGraph. `contracts`, `agents`, `rag`
y `mcp` no conocen el framework del grafo.
