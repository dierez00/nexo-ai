"""Agentes de Nexo IA (Fase 1).

Cada agente es una unidad con una responsabilidad, una entrada tipada y una
salida tipada. Ninguno abre una base de datos, conoce FastAPI ni importa el SDK
de un proveedor: el modelo llega por `ChatModelPort`, la evidencia por
`RetrieverPort` y las tools por `ToolExecutorPort`, todos inyectados desde la
orquestación.

Dos reglas transversales, verificadas por contrato y no por disciplina:

- solo el agente transaccional puede proponer o ejecutar tools de escritura
  (`AgentResult` rechaza lo contrario);
- el redactor recibe únicamente `VerifiedFacts` y no tiene puertos de RAG ni de
  MCP en su constructor (`DIE-F1-094`).
"""
