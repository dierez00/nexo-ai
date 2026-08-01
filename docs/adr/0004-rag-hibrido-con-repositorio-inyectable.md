# 0004 — RAG híbrido PostgreSQL FTS + pgvector con repositorio inyectable

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Estado:** accepted
- **Revisión:** schema, índices y migraciones de persistencia
- **Tarea:** `DIE-F0-004`

## Contexto

Las consultas ciudadanas mezclan términos exactos que deben coincidir literalmente
(«uso de suelo», «licencia tipo A») con paráfrasis que solo la similitud
semántica recupera («quiero poner una taquería»). Una sola estrategia falla en
la mitad de los casos. Además, el gate exige recall@5 ≥ 0.80 y citation
precision ≥ 0.90 sin cruces de institución, dominio ni vigencia.

## Opciones consideradas

| Opción | A favor | En contra |
|---|---|---|
| **PostgreSQL FTS + pgvector** | Un solo motor para operación, vectores, auditoría y checkpoints; transacciones y backups unificados | pgvector escala peor que un motor vectorial dedicado a gran volumen |
| Solo búsqueda vectorial | Simple | Falla en términos exactos y en nombres de trámite |
| Qdrant / Weaviate | Mejor a gran escala | Segunda persistencia que respaldar, migrar y mantener consistente |
| Chroma local | Trivial de arrancar | Duplica persistencia y no sobrevive al despliegue |

## Decisión

**Búsqueda híbrida sobre PostgreSQL** (FTS lexical + pgvector semántico) con
fusión determinista, detrás de `RetrieverPort`.

Reglas que el puerto impone, no el motor:

1. **Los filtros se aplican antes de puntuar.** Institución, dominio, estado y
   vigencia no son un post-filtro: un fragmento que no los satisface no compite,
   ni con puntaje alto.
2. **Toda respuesta trae `corpus_version` y citaciones completas.** Un resultado
   sin `source_id` y `fragment_id` no puede sostener un claim crítico.
3. **La fusión es determinista y estable ante empates.** El desempate es por
   `fragment_id`; sin él, dos fragmentos con el mismo puntaje alternarían de
   orden entre corridas y ningún baseline sería comparable.
4. **El contenido recuperado es dato, nunca instrucción.** Los patrones de
   prompt injection se registran en `injection_signals` y el fragmento se
   entrega marcado; no se obedece ni se descarta en silencio.
5. **El repositorio es inyectable.** El doble en memoria de Fase 0 aplica los
   mismos filtros lógicos que aplicará el repositorio real, de modo que una
   prueba que pasa con el doble siga significando algo con PostgreSQL.

## Consecuencias

**A favor**

- Una sola base de datos que respaldar, migrar y auditar.
- Las pruebas de aislamiento de namespace corren sin PostgreSQL.
- Cambiar el motor vectorial no toca agentes ni contratos.

**En contra**

- El doble en memoria puntúa con una heurística léxica, no con embeddings
  reales: sirve para verificar filtros y orden, **no** para medir recall. El
  baseline de calidad exige el retriever real (Fase 1, F1.3).
- pgvector impondrá un techo de escala que habrá que medir antes de llegar a él.

## Evidencia

- `rag/src/nexo_rag/ports.py`, `rag/src/nexo_rag/testing/retriever.py`
- `rag/tests/test_retriever.py` — fuente vencida, sustituida, otra institución y
  otro dominio quedan fuera; el orden es reproducible.

## Criterio de reevaluación

Se reabre cuando una medición muestre que pgvector no sostiene la latencia
objetivo con el corpus real, o cuando el corpus supere el volumen que un solo
PostgreSQL indexa cómodamente.
