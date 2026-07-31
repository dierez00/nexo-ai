# Workflow event mapping v1

Contrato de entrega para Cris (`DIE-F2-061`). La fuente de verdad es
`RunEvent`; el renderer no infiere pasos desde texto libre.

## Versión

- Mapping: `workflow-event-mapping-v1`
- Catálogo Core: `core-catalog-2026-07-30`
- Correlación: `correlation_id`
- Jerarquía: `parent_event_id`
- Orden: `sequence`, estrictamente creciente y sin huecos por `run_id`
- Grafo MVP: `normalize → classify → plan → retrieve → navigate → read_tools → verify → estimate → merge → build_a2ui → write_answer → finalize`

## Familias estables

| Prefijo de `type` | Nodo visual |
|---|---|
| `run.*` | estado del run |
| `classification.*`, `agent.*` | agente/nodo |
| `plan.*` | supervisor |
| `rag.*` | retrieval |
| `tool.*` | herramienta |
| `model.*` | modelo |
| `verification.*`, `contradiction.*` | verificación |
| `checkpoint.*` | checkpoint |
| `a2ui.*` | superficie |
| `evaluation.*` | evaluación |

`public_data` es la única carga apta para una vista pública. `data` es la carga
restringida de auditoría. Si `visibility` es `restricted`, el actor se proyecta
como `restringido`; nunca se usa `data` como fallback.

Los fixtures `success`, `partial`, `retry`, `permission_denied` y
`confirmation` se publican tanto en `orchestration/fixtures/workflow/` como en
`apps/web/public/fixtures/workflow/`. Cada archivo incluye eventos crudos y el
replay esperado para pruebas cruzadas.
