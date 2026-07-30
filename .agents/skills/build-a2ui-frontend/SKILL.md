---
name: build-a2ui-frontend
description: Construye y modifica frontends de Nexo IA con Next.js, TypeScript, Tailwind CSS, shadcn/ui y Radix; crea componentes modernos y responsivos, sistemas de diseño, shells y pantallas base para portal o administración, y superficies declarativas compatibles con A2UI v0.9.1. Usar al preparar interfaces nuevas, ampliar el catálogo A2UI, mapear componentes React, crear fixtures JSONL, implementar estados de interfaz o endurecer accesibilidad, responsive y fallbacks seguros.
---

# Construir frontends A2UI

## Principios

- Tratar A2UI como entrada no confiable y renderizar únicamente componentes registrados.
- Mantener estructura, datos y acciones separados; no ejecutar HTML, JavaScript ni handlers recibidos.
- Reutilizar contratos, tokens, componentes y convenciones existentes antes de crear otros.
- Diseñar mobile-first y cumplir WCAG 2.2 AA, teclado, foco visible y reduced motion.
- Mantener explícitos los estados loading, empty, error, partial, offline y fallback.
- Usar texto orientado a la persona: verbos claros, sentence case y acciones con nombres consistentes.

## Flujo

### 1. Inspeccionar el proyecto

1. Leer `README`, contratos A2UI, configuración de Next/Tailwind/shadcn, package manager y componentes existentes.
2. Confirmar la versión fijada de A2UI. Para Nexo usar v0.9.1 y los imports versionados `@a2ui/react/v0_9` y `@a2ui/web_core/v0_9`.
3. Detectar cambios locales y preservar decisiones o ediciones ajenas.
4. Clasificar el trabajo como sistema de diseño, componente, surface A2UI, portal, administración o combinación.

### 2. Fijar la dirección visual

Antes de escribir código, declarar de forma compacta:

- sujeto, audiencia y único trabajo principal de la vista;
- 4–6 tokens de color semánticos;
- roles tipográficos;
- concepto de layout;
- una sola firma visual vinculada al dominio.

Revisar la propuesta contra el brief. Sustituir cualquier elección que pudiera pertenecer sin cambios a otro producto. Mantener el resto sobrio y funcional.

Leer [references/design-system.md](references/design-system.md) antes de crear o modificar tokens, componentes o estilos.

### 3. Preparar la base

1. Respetar el package manager y versiones del proyecto; no reinstalar ni migrar el stack sin necesidad.
2. Reutilizar shadcn/ui existente. Si falta, configurarlo sobre Tailwind y Radix conservando aliases y CSS actuales.
3. Copiar o adaptar desde `assets/starter/` únicamente las piezas necesarias; no sobrescribir archivos completos sin integrar sus diferencias.
4. Modelar variantes con props tipadas y CVA. Mantener detalles visuales fuera del contrato A2UI.
5. Usar tokens CSS semánticos para color, tipografía, espacio, radio, sombra, densidad y movimiento.

### 4. Construir componentes e interfaces

- Preferir HTML semántico y primitivas Radix para interacción compleja.
- Hacer serializables las props expuestas a A2UI; no exponer `className`, `style`, `dangerouslySetInnerHTML`, HTML, SVG arbitrario ni callbacks.
- Incluir label, descripción, estado deshabilitado, errores, foco y nombres accesibles donde corresponda.
- Componer portal y administración con las recetas de [references/interface-recipes.md](references/interface-recipes.md).
- Conservar usable la vista desde 360 px; transformar tablas densas en tarjetas o scroll contenido, nunca en overflow global.
- Usar movimiento solo si comunica estado o relación; respetar `prefers-reduced-motion`.

### 5. Integrar A2UI

Leer [references/a2ui-v0.9.1.md](references/a2ui-v0.9.1.md) antes de tocar catálogos, renderer, bindings, acciones o JSONL.

1. Partir del catálogo básico oficial y registrar adaptadores React confiables.
2. Usar el catálogo ciudadano `urn:nexo-ia:a2ui:catalog:citizen:v1` o el administrativo `urn:nexo-ia:a2ui:catalog:admin:v1`; no reutilizar uno para el otro.
3. Declarar relaciones con `ComponentId` y `ChildList`, y datos reactivos mediante JSON Pointer.
4. Enviar acciones opacas al servidor; bloquear doble envío y mostrar confirmación, progreso y resultado recuperable.
5. Validar schema, catálogo, árbol, bindings y acciones antes de renderizar.
6. Mostrar un fallback seguro ante una surface inválida sin revelar el payload.
7. Descartar y recrear el procesador después de un error de validación; no conservar una surface parcial.

### 6. Verificar y criticar

1. Ejecutar typecheck, lint y pruebas del proyecto.
2. Ejecutar pruebas de componente, accesibilidad y contrato A2UI.
3. Ejecutar Playwright para los recorridos afectados cuando exista la aplicación.
4. Auditar fixtures con:

```bash
python3 .agents/skills/build-a2ui-frontend/scripts/audit_a2ui.py \
  --catalog ruta/catalog.json \
  --fixture ruta/surface.jsonl
```

5. Revisar visualmente móvil, tablet y escritorio; capturar screenshots si hay navegador disponible.
6. Comprobar contraste, foco, zoom, teclado, reduced motion, textos largos, datos vacíos y errores.
7. Eliminar decoración sin función y confirmar que la firma visual siga siendo propia del brief.

## Recursos

- `assets/starter/tokens.css`: base institucional clara/oscura y aliases A2UI.
- `assets/starter/components.json`: configuración shadcn adaptable.
- `assets/starter/a2ui/`: catálogos, registro React, guard de mensajes, componentes semánticos, política de URL y fallback.
- `assets/fixtures/`: ejemplos válidos y casos inválidos para probar rechazo.
- `scripts/audit_a2ui.py`: auditor determinista de catálogos y streams JSONL.

No copiar recursos por defecto. Seleccionar, adaptar y probar solo los que resuelvan el pedido.
