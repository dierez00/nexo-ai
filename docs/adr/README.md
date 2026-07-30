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
