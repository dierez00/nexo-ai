# Recetas de interfaces base

## Shell compartido

Incluir:

- skip link y landmarks;
- encabezado con identidad, estado de sesión y ayuda;
- navegación consistente por rol;
- región de notificaciones;
- contenido con ancho adaptado a lectura o trabajo;
- boundary de error y estado offline;
- tema claro/oscuro sin flash inicial.

En móvil convertir navegación lateral en drawer Radix. Mantener el título y la acción principal accesibles sin sticky overlays invasivos.

## Autenticación

Preparar login, sesión expirada, acceso denegado y recuperación:

- explicar la acción disponible, no el mecanismo de autenticación;
- conservar destino seguro después de reautenticar;
- no revelar si una cuenta existe;
- enfocar el primer error útil;
- nunca representar visibilidad del cliente como permiso efectivo.

## Portal ciudadano

Componer:

1. **Inicio:** solicitudes recientes, trámite sugerido y acceso al chat.
2. **Chat:** historial, composer, streaming, fuentes y zona A2UI.
3. **Trámite:** estado, requisitos, documentos, costos, pasos y fuentes.
4. **Citas:** filtros mínimos, slots, resumen y confirmación idempotente.
5. **Seguimiento:** folio, timeline, próxima acción y canal de ayuda.

Usar `SourceCitation`, `Checklist`, `StatusBanner` y `ConfirmationSummary` solo cuando aporten semántica; componer el resto con el catálogo básico.

Estados obligatorios:

- conversación vacía con ejemplos útiles;
- respuesta en streaming;
- datos parciales con lo conocido y lo faltante;
- fuente no disponible;
- acción pendiente, confirmada, duplicada o fallida;
- surface inválida con fallback textual.

## Administración

Componer:

1. **Dashboard:** rango/filtros, métricas, tendencias y calidad del dato.
2. **Runs:** tabla filtrable y detalle por `trace_id`.
3. **Workflow:** grafo accesible, timeline de eventos y panel de inspección.
4. **Catálogo:** estado de agentes, tools, fuentes y versiones A2UI.
5. **Integraciones:** salud, última ejecución y errores recuperables.

Usar `MetricCard` como resumen, no como decoración. Acompañar cambios con periodo y contexto. Usar `DataTable` para comparación exacta, `RunTimeline` para secuencia y `WorkflowGraph` para dependencias.

En móvil:

- apilar métricas;
- mostrar filas como tarjetas etiquetadas cuando se pierda legibilidad;
- ofrecer el grafo como lista ordenada equivalente;
- mover filtros secundarios a un sheet accesible.

## Chat y surfaces

Separar visualmente:

- texto redactado;
- hechos verificados;
- fuentes;
- interfaz A2UI;
- acciones que escriben datos.

No insertar la surface dentro de un globo estrecho. Darle ancho suficiente, mantenerla conectada al mensaje que la originó y anunciar actualizaciones relevantes sin mover el foco.

## Copy de estados

- Loading: describir qué se está consultando.
- Empty: explicar qué puede hacer la persona.
- Error: decir qué ocurrió y cómo continuar.
- Partial: distinguir lo disponible de lo pendiente.
- Success: repetir el nombre exacto de la acción completada.

Evitar “Enviar” si el resultado real es “Reservar cita”, “Guardar cambios” o “Generar folio”.

## Criterios de salida

- Portal y admin funcionan con teclado y a 360 px.
- Cada vista tiene un trabajo principal evidente.
- La acción primaria conserva el mismo verbo hasta la confirmación.
- Las fuentes y estados mock/partial son visibles.
- La interfaz inválida degrada sin ejecutar código.
- Los roles protegen rutas en servidor y las acciones vuelven a validar permisos.
