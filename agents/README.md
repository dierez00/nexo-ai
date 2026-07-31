# Agentes

## Objetivo

Definir agentes transversales con responsabilidades, herramientas y salidas estrictamente limitadas.

## Debe contener

Clasificador, verificador, estimador, transaccional, redactor, judge y prompt assistant; prompts versionados y modelos Pydantic.

## No debe contener

Servidor HTTP, conexiones DB, secretos, componentes UI ni acceso libre a RAG/tools.

## Convenciones

Un agente por módulo; entrada/salida tipadas; autoverificación; timeout, presupuesto, sources y tool allowlist declarados. El redactor solo acepta `VerifiedFacts`.

## Dependencias y responsable

Depende de `contracts`; RAG/MCP se inyectan desde orquestación. Responsable: Diego.

## Ejemplos y tareas

`classifier.py`, `verifier.py`, `outputs.py`, `prompts/v1.md`. Empezar por modelos falsos y agentes MVP, después guardrails y evals.

## Terminado

Cada agente pasa schema, permisos y tests deterministas sin proveedor real; no produce claims críticos sin fuente.

## Estado tras Fase 1

Implementados clasificador, navegadores de vehículos/empresas, verificador,
estimadores deterministas, agente transaccional y redactor cerrado. Los
manifiestos y skills YAML fijan prompts, fuentes, tools y pasos permitidos; los
resultados MCP se convierten a hechos conservando su `tool_call_id`.

Judge, prompt assistant y dominios posteriores pertenecen a fases posteriores.
