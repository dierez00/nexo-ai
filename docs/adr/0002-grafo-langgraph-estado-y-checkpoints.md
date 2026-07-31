# 0002 — Grafo LangGraph, estado serializable y política de checkpoints

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Decisor:** Diego
- **Revisan:** Dani (ejecución y API), Daher (persistencia de checkpoints)
- **Tarea:** `DIE-F0-002`

## Contexto

El núcleo debe coordinar cinco dominios, pausar antes de cada escritura para
pedir confirmación, reanudar sin duplicar efectos y, en Fase 4, ejecutar el
verificador y el estimador en paralelo con un merge independiente del orden de
llegada. Nada de eso es viable sobre una cadena de llamadas ad hoc: exige estado
explícito, transiciones observables y checkpoints reproducibles.

## Opciones consideradas

| Opción | A favor | En contra |
|---|---|---|
| **LangGraph** | Estado, ramas, checkpoints e interrupciones como primitivas; ecosistema amplio | Dependencia externa con superficie propia; su modelo de estado tiende a filtrarse al dominio |
| PydanticAI Graph | Menos dependencias, muy alineado con Pydantic | Ecosistema pequeño; menos maduro en checkpoints e interrupts |
| Orquestador propio | Control total y cero dependencias | Reimplementar checkpoints, fan-in determinista y reanudación es trabajo caro y ya resuelto |
| CrewAI | Rápido para prototipos conversacionales | Menos control explícito sobre un grafo auditable |

## Decisión

Se usa **LangGraph** como motor del grafo, desde Fase 0, con tres restricciones:

1. **El estado del dominio es `RunState`, un contrato Pydantic propio.** LangGraph
   transporta un `GraphState` local de la orquestación que lo envuelve. Los
   contratos publicados no importan LangGraph ni conocen sus reducers.
2. **`RunState` es serializable siempre.** No admite clientes, handles,
   corrutinas ni secretos. La restricción no es una convención: los campos de
   forma libre son `SafePayload` (JSON puro sin claves de secreto ni PII), así
   que un objeto vivo falla en validación.
3. **Los checkpoints usan un puerto propio** (`CheckpointStorePort`), no el
   checkpointer del framework. Lo que se persiste es `RunState`, que es lo que
   Daher almacenará en PostgreSQL.

Política de checkpoints:

- se guarda tras **cada nodo completado**, y en Fase 1 también antes de cada
  interrupt de confirmación y después de cada merge;
- el nodo confirmado se registra en `completed_nodes`; reanudar no lo reejecuta;
- el evento `checkpoint.saved` se emite **antes** de persistir, para que el
  `event_cursor` guardado coincida con los eventos realmente emitidos;
- el identificador del checkpoint viene de la `IdFactory` inyectada, no de un
  contador interno del almacén, para que sea reproducible.

## Consecuencias

**A favor**

- Fan-out, interrupts y reanudación se apoyan en primitivas probadas.
- El estado sobrevive a un reinicio y el run se reconstruye por `trace_id`.
- Sustituir el almacén en memoria por PostgreSQL no toca el grafo.

**En contra**

- LangGraph arrastra `langchain-core` y dependencias transitivas. Se acota a
  `orchestration`: ni `contracts`, ni `agents`, ni `rag`, ni `mcp` lo importan.
- Mantener dos nociones de checkpoint (la del framework y la nuestra) obliga a
  documentar cuál manda. Manda la nuestra.

## Evidencia

- `orchestration/src/nexo_orchestration/graph/minimal.py`
- `orchestration/tests/test_graph.py` — reanudación sin reejecución, deadline,
  coherencia entre `event_cursor` y traza.
- El orden «guardar y luego emitir» produjo una colisión de secuencia real al
  reanudar, detectada por `test_resume_continues_the_event_sequence`.

## Criterio de reevaluación

Se reabre si: LangGraph introduce un cambio incompatible que obligue a alterar
`RunState`; el grafo necesita distribuirse entre procesos; o el costo de
mantener la envoltura supera lo que aporta el framework.
