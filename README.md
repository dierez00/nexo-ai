# Nexo IA

## Objetivo

Hub omnicanal de asistentes e integración institucional. El núcleo Python de
las Fases 0 y 1 ya es ejecutable completamente offline; las aplicaciones web,
la API y las integraciones externas avanzan en módulos separados.

## Documentos principales

- [`Nexo_IA_Propuesta_Completa.md`](./Nexo_IA_Propuesta_Completa.md): problema, alcance y rúbrica.
- [`Nexo_IA_Arquitectura_y_Plan.md`](./Nexo_IA_Arquitectura_y_Plan.md): arquitectura, contratos, fases, pruebas y despliegue.
- [`docs/team/`](./docs/team/): división de trabajo para Cris, Dani, Daher y Diego.

## Alcance acordado

- MVP: vehículos y apertura de empresas de extremo a extremo, con transacciones mock, WhatsApp Twilio Sandbox y una sola app web con `/portal` y `/admin`.
- Core: cinco dominios, workflow, dashboard y catálogo.
- Pro: voz, MCP Mapper, model router y A2UI dinámico.
- Extremo: paralelismo, mini-RAGs, LLM-as-judge y personalización avanzada.

## Estado de ejecución

Los comandos `docker compose up --build` y `./run.sh` son entregables futuros. No se documentan como disponibles hasta que existan y tengan un smoke test.

### Núcleo Python (Fases 0 y 1 — `implementadas`)

Existe un workspace Python con contratos tipados, puertos, dobles de prueba,
configuración validada y un grafo mínimo verificable. Corre **sin red, sin base
de datos y sin credenciales**.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e ./contracts -e ./rag -e ./mcp \
  -e ./orchestration -e ./agents -e ./a2ui
.venv/bin/python -m pip install pytest pytest-asyncio ruff
.venv/bin/python -m pytest -c pyproject.toml \
  contracts/tests orchestration/tests rag/tests mcp/tests agents/tests \
  a2ui/tests tests/e2e
```

Regenerar los artefactos derivados de `contracts/` tras cambiar un modelo:

```sh
.venv/bin/python -m nexo_contracts.export
```

Alcance actual: contratos versionados, corpus y retrieval híbrido, agentes
cerrados, server/tools MCP mock, grafo MVP reanudable con confirmación,
estimación determinista y A2UI ciudadano con fallback. Los recorridos
`CAP-VEH-01` y `CAP-EMP-01` se prueban de extremo a extremo sin credenciales.
Ver [`docs/team/fase1_hallazgos.md`](./docs/team/fase1_hallazgos.md).

## Convenciones

- Marcar capacidades como `planeada`, `mock` o `implementada`.
- No versionar secretos ni PII real.
- Cambiar contratos mediante revisión conjunta.
- Mantener documentación y estado real sincronizados.

## Dependencias, ejemplos y tareas

La raíz enlaza todos los módulos, pero no contiene lógica de uno en particular. Archivos ejemplo futuros: `compose.yaml`, `.env.example` y `run.sh`. Tareas iniciales: bootstrap, healthchecks, seed E2E y guion.

Responsable de instalación futura: Dani. Todo el equipo valida alcance y demo. La raíz se considera terminada cuando una persona nueva puede comprender y ejecutar el proyecto sin ayuda.

## Skill de frontend

Usa `$build-a2ui-frontend` para interfaces y futuros catálogos compatibles con
A2UI v0.9.1. `citizen:v1` está congelado: cualquier evolución funcional publica
`citizen:v2`. La skill versionada está en
`.agents/skills/build-a2ui-frontend`.
