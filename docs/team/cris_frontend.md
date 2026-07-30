# Cris — frontend

## 1. Objetivo general

Entregar una experiencia web accesible para ciudadanos y administradores que consuma contratos estables, represente A2UI y visualice trazas reales sin duplicar reglas del backend.

## 2. Responsabilidades

- Next.js, `/portal` y `/admin`.
- Sesión, navegación, chat, streaming y carga de archivos.
- Renderer del catálogo A2UI y fallbacks.
- Workflow tipo n8n y dashboards.
- Accesibilidad, responsive, estados de error/partial y pruebas UI.

## 3. Carpetas bajo responsabilidad

Principal: `apps/web`. Apoyo: `a2ui`, `contracts/examples`, `tests/e2e`, `data/assets` y `docs`.

## 4. Tareas MVP

- Configurar shell, rutas, layout y sesión.
- Consumir cliente OpenAPI y SSE reanudable.
- Construir chat, panel de fuentes, checklists, costos, slots y confirmación.
- Renderizar catálogo A2UI MVP sin HTML/JS arbitrario.
- Completar vehículos y apertura de empresas en Playwright.

## 5. Tareas Core

- Añadir tres dominios a la experiencia.
- Mostrar workflow/timeline desde eventos.
- Dashboard básico, filtros y perfiles.
- Diseñar estados de error, timeout, partial y fallback multicanal.

## 6. Tareas Pro

- Formularios A2UI dinámicos.
- Interfaces administrativas generadas desde consultas autorizadas.
- Experiencia vinculada para conversaciones iniciadas por voz/WhatsApp.

## 7. Tareas Extremo

- Builder visual del flujo.
- Comparación modelo/costo/latencia/precisión.
- Personalización por audiencia y surfaces administrativas avanzadas.

## 8. Entregables concretos

App compilable, rutas protegidas, catálogo visual, cliente generado, renderer, workflow, dashboards, componentes accesibles, tests Vitest/Testing Library/Playwright y README actualizado.

## 9. Dependencias con otros integrantes

- Dani: OpenAPI, auth, SSE, errores y acciones.
- Diego: schemas A2UI, catálogo, eventos y fixtures.
- Daher: seeds, métricas y datos administrativos.

## 10. Contratos de integración

- Acceso solo mediante API; nunca DB.
- Propagar `trace_id` y `Last-Event-ID`.
- En confirmaciones enviar `action_id`, versión e `idempotency_key`.
- Tratar A2UI como input no confiable y validar catálogo/acciones.
- Respetar Problem Details y no deducir permisos en cliente.

## 11. Riesgos y coordinación

Cambios de catálogo, eventos fuera de orden, diferencias de canal, acciones duplicadas, auth visible pero no efectiva y gráficas sin datos suficientes. Congelar fixtures por fase y revisar contratos antes de integrar.

## 12. Pruebas a implementar

Componentes, accesibilidad, rutas por rol, contract fixtures, SSE reconnect, A2UI inválido, clicks duplicados, loading/error/partial, responsive y dos E2E MVP; ampliar a cinco en Core.

## 13. Criterios de aceptación

- Portal/admin operables por teclado.
- Fuentes y estado mock visibles.
- Cero ejecución de código generado.
- Acciones bloqueadas mientras se confirman y errores recuperables.
- Tests de contrato, accesibilidad y E2E verdes.

## 14. Orden recomendado

Workspace → shell/auth → cliente contrato → chat/SSE → A2UI → citas/acciones → admin → workflow → dashboards → endurecimiento/tests.

## 15. Checklist

- [ ] Rutas y layouts.
- [ ] Loading, empty, error y partial.
- [ ] Roles y expiración de sesión.
- [ ] Cliente OpenAPI/SSE.
- [ ] Renderer y fallbacks A2UI.
- [ ] Fuentes y masking.
- [ ] Confirmaciones idempotentes.
- [ ] Workflow/dashboard.
- [ ] Responsive/accesibilidad.
- [ ] Unit, contract y E2E.
- [ ] README/guion de demo.

## 16. Paralelismo y bloqueos

Puede construir UI completa con fixtures desde Fase 0. La integración real queda bloqueada por OpenAPI/auth/SSE de Dani; el workflow por eventos de Diego; dashboards por seeds/queries de Daher. A2UI se trabaja en paralelo: Diego produce schema/fixtures y Cris renderer/snapshots.

## Funcionalidades compartidas

| Funcionalidad | Principal | Apoyo | Contrato | Entregable | Integración |
|---|---|---|---|---|---|
| A2UI renderer | Cris | Diego | Catalog/JSONL | Renderer + fixtures | MVP antes de E2E |
| Chat/SSE | Dani | Cris | OpenAPI/events | Conversación web | MVP |
| Workflow | Cris | Diego | RunEvent | Grafo/timeline | Core |
| Dashboard | Cris | Daher/Dani | MetricSet | Paneles | Core |
