# Mapeo de eventos del workflow v1

La fuente de verdad del workflow es `RunEvent`; la interfaz no infiere pasos
desde texto libre. `public_data` es la única carga apta para la vista pública y
`data` queda restringida a auditoría.

## Secuencia

`normalize → classify → plan → retrieve → navigate → read_tools → verify →
estimate → merge → build_a2ui → write_answer → finalize`

## Familias visuales

| Prefijo | Representación |
| --- | --- |
| `run.*` | Estado de la ejecución |
| `classification.*`, `agent.*` | Agente o nodo |
| `plan.*` | Supervisor |
| `rag.*` | Recuperación documental |
| `tool.*` | Herramienta |
| `model.*` | Modelo |
| `verification.*`, `contradiction.*` | Verificación |
| `checkpoint.*` | Checkpoint |
| `a2ui.*` | Superficie |
| `evaluation.*` | Evaluación |

Los replays de éxito, parcialidad, reintento, permiso denegado y confirmación
se mantienen como fixtures cruzados entre orquestación y frontend.
