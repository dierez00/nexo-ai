# Nexo IA

## Objetivo

Hub omnicanal de asistentes e integración institucional. El repositorio se encuentra en **fase de arquitectura documental**: todavía no contiene una aplicación ejecutable.

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

## Convenciones

- Marcar capacidades como `planeada`, `mock` o `implementada`.
- No versionar secretos ni PII real.
- Cambiar contratos mediante revisión conjunta.
- Mantener documentación y estado real sincronizados.

## Dependencias, ejemplos y tareas

La raíz enlaza todos los módulos, pero no contiene lógica de uno en particular. Archivos ejemplo futuros: `compose.yaml`, `.env.example` y `run.sh`. Tareas iniciales: bootstrap, healthchecks, seed E2E y guion.

Responsable de instalación futura: Dani. Todo el equipo valida alcance y demo. La raíz se considera terminada cuando una persona nueva puede comprender y ejecutar el proyecto sin ayuda.
