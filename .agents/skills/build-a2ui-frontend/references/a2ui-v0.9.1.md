# A2UI v0.9.1 en Nexo

## Contenido

- Fuentes canónicas y runtime
- Mensajes, lifecycle y catálogos
- Datos y acciones
- Seguridad y fallback
- Transporte y compatibilidad

## Fuentes canónicas

- Protocolo actual: <https://a2ui.org/specification/v0.9.1-a2ui/>
- Configuración React: <https://a2ui.org/guides/client-setup/>
- Desarrollo de renderers: <https://a2ui.org/guides/renderer-development/>

Usar v0.9.1. No mezclar estructuras de v0.8 ni adelantar contratos de v1.0.

## Runtime

Instalar o reutilizar:

```text
@a2ui/react
@a2ui/web_core
zod
```

Importar las APIs versionadas:

```ts
import { A2uiSurface, basicCatalog } from "@a2ui/react/v0_9";
import { Catalog, MessageProcessor } from "@a2ui/web_core/v0_9";
```

Crear `MessageProcessor` con `{ version: "v0.9.1" }`. Dejar que `web_core` procese mensajes, surfaces, bindings y funciones; no reimplementar ese estado.

## Mensajes y lifecycle

Aceptar solo JSONL con una unidad JSON por línea y `version: "v0.9.1"`.

1. Crear con `createSurface`.
2. Actualizar estructura con `updateComponents`.
3. Actualizar datos con `updateDataModel`.
4. Eliminar con `deleteSurface`.

Exigir `createSurface` antes de cualquier actualización. Mantener `surfaceId` y `catalogId` inmutables durante la vida de la surface. Exigir exactamente un componente `root`.

## Catálogos

Usar IDs inmutables:

- Ciudadano: `urn:nexo-ia:a2ui:catalog:citizen:v1`
- Administración: `urn:nexo-ia:a2ui:catalog:admin:v1`

Mapear el catálogo básico completo:

`Text`, `Image`, `Icon`, `Video`, `AudioPlayer`, `Row`, `Column`, `List`, `Card`, `Tabs`, `Divider`, `Modal`, `Button`, `CheckBox`, `TextField`, `DateTimeInput`, `ChoicePicker` y `Slider`.

Registrar extensiones:

| Catálogo | Extensiones |
|---|---|
| Ambos | `StatusBanner`, `SourceCitation`, `Checklist` |
| Ciudadano | `ConfirmationSummary` |
| Administración | `MetricCard`, `DataTable`, `RunTimeline`, `WorkflowGraph` |

Referenciar hijos individuales mediante `common_types.json#/$defs/ComponentId` y listas mediante `common_types.json#/$defs/ChildList`. Mantener `additionalProperties`/`unevaluatedProperties` cerrados.
Mantener `DataTable` de solo lectura hasta versionar una acción de fila opaca. Enlazar
`WorkflowGraph.nodes` y `WorkflowGraph.edges` al modelo de datos para actualizaciones
incrementales; limitar el renderer a 100 nodos y 200 conexiones.

## Datos

- Usar literales o `{ "path": "/ruta" }` según el tipo dinámico.
- Usar JSON Pointer absoluto desde la raíz.
- Usar rutas relativas únicamente dentro de templates de `ChildList`.
- Tratar bindings todavía no disponibles como loading/undefined, no como error fatal.
- Enviar cambios de inputs al servidor solo mediante una acción explícita.
- Precalcular formatos sensibles en servidor cuando formen parte de hechos verificados.

## Acciones

- Aceptar únicamente `event` o `functionCall` registrados.
- Mantener nombres de evento opacos y estables.
- Incluir `action_id` e `idempotency_key` en el contexto de confirmaciones cuando el contrato los requiera.
- Volver a validar permisos, datos e idempotencia en servidor.
- Deshabilitar acciones durante el envío y permitir recuperación después de error.
- Permitir `openUrl` solo después de pasar una política explícita de protocolo y host.

Ocultar un botón nunca sustituye autorización server-side.

## Seguridad

Rechazar antes de renderizar:

- catálogo o componente desconocido;
- IDs duplicados, referencias ausentes o ciclos de lifecycle;
- `className`, `style`, `dangerouslySetInnerHTML`, HTML, SVG arbitrario o claves `on*`;
- esquemas abiertos sin justificación;
- URLs con protocolo no permitido;
- handlers, código o funciones no registradas;
- bindings inválidos y acciones mal formadas.

No registrar un componente dinámicamente a partir del payload. No mostrar el payload inválido en el fallback.

## Fallback

Mostrar una superficie estable con:

- título: “No pudimos mostrar esta información”;
- explicación breve sin detalles internos;
- acción segura para reintentar o continuar en formato textual;
- `trace_id` solo si la política permite mostrarlo.

Enviar un error `VALIDATION_FAILED` estructurado al servidor u observabilidad.
Si el procesador recibió parte de un lote que terminó en error, descartar esa instancia y
crear una nueva antes del reintento. No volver a procesar directamente los bytes rechazados.

## Transporte

Para SSE/JSONL:

- conservar orden;
- separar correctamente cada mensaje;
- reanudar con `Last-Event-ID` cuando el contrato lo permita;
- deduplicar eventos;
- marcar estados parciales;
- no aplicar mensajes a una surface eliminada.

## Compatibilidad

Crear un nuevo ID de catálogo para cualquier cambio incompatible. Mantener fixtures de cada versión y contract tests compartidos entre builder y renderer.
