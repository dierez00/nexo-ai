# Sistema de diseño frontend

## Dirección visual

Definir primero el contexto real de la interfaz:

- **Sujeto:** trámite, operación institucional o supervisión que representa.
- **Audiencia:** ciudadano, operador, supervisor, analista o desarrollador.
- **Trabajo principal:** una acción o decisión verificable por vista.
- **Firma:** un recurso visual propio del dominio; para Nexo puede ser un riel de trazabilidad que conecte estado, fuente y siguiente acción.

Proponer 4–6 colores con nombre y valor, roles tipográficos, layout y firma. Mantener la identidad institucional flexible: sobria, legible y tematizable, sin convertir “institucional” en una cuadrícula azul genérica.

## Tokens

Usar variables semánticas, nunca colores de marca dispersos:

- Superficie: `background`, `surface`, `surface-muted`, `overlay`.
- Texto: `foreground`, `muted-foreground`, `inverse-foreground`.
- Acción: `primary`, `primary-foreground`, `secondary`, `accent`.
- Estado: `success`, `warning`, `danger`, `info`.
- Estructura: `border`, `input`, `ring`.
- Forma: radios, sombras y espacios con una escala corta.

Mantener light/dark en las mismas variables. No usar el color como único indicador. Ver `assets/starter/tokens.css` como base, no como branding final.

## Stack

- Usar Next.js App Router y componentes de servidor por defecto.
- Añadir `"use client"` únicamente en fronteras interactivas.
- Mantener TypeScript estricto y props exportadas.
- Usar Tailwind para composición y tokens; usar CVA para variantes.
- Usar shadcn/ui como código local y Radix para semántica, teclado y manejo de foco.
- Preferir Lucide o el set ya instalado; no aceptar SVG arbitrario desde A2UI.
- Respetar el alias y la convención de imports existentes.

No ejecutar `shadcn init` sobre una configuración existente. Añadir componentes puntuales y revisar el diff.

## Componentes

Para cada componente:

1. Definir propósito y elemento HTML correcto.
2. Mantener API pequeña y serializable.
3. Separar variante semántica de detalles cosméticos.
4. Añadir estados default, hover, focus-visible, active, disabled, loading y error cuando apliquen.
5. Mantener objetivos táctiles de al menos 44 × 44 CSS px cuando la densidad lo permita.
6. Asociar label, descripción y error mediante IDs.
7. Probar textos largos, zoom 200 %, viewport de 360 px y modo oscuro.

No exponer a A2UI:

- `className`, `style`, nombres de clases o tokens internos;
- HTML/Markdown con HTML, SVG paths o componentes importables;
- callbacks, expresiones, URLs `javascript:` o atributos `on*`;
- tamaños o posiciones absolutas que rompan el layout.

## Responsive

- Empezar en una columna y añadir columnas solo cuando el contenido lo justifique.
- Usar `minmax(0, 1fr)` y `min-w-0` en hijos flex/grid.
- Limitar el ancho de lectura; no limitar paneles de trabajo que necesitan datos densos.
- Convertir navegación lateral en drawer accesible en móvil.
- Transformar tablas en tarjetas etiquetadas o contener su scroll horizontal.
- Mantener acciones primarias visibles sin tapar contenido ni depender de hover.
- Reservar espacio de contenido que llega por streaming para reducir saltos de layout.

## Accesibilidad WCAG 2.2 AA

- Mantener orden DOM coherente con el orden visual.
- Usar landmarks, encabezados jerárquicos y skip link.
- Conservar contraste AA y foco que no quede oculto.
- Operar dialogs, tabs, menus y popovers completamente con teclado.
- Anunciar cambios asíncronos relevantes con regiones live sin repetir todo el contenido.
- Asociar errores al campo y explicar cómo corregirlos.
- Respetar `prefers-reduced-motion` y evitar parpadeos.
- No bloquear zoom ni orientación.

## Autocrítica

Antes de entregar:

- Identificar qué elección pertenece específicamente al brief.
- Quitar una decoración que no comunique información.
- Confirmar que la tipografía y el layout no sean presets indiferenciados.
- Revisar que el copy nombre lo que la persona controla, no detalles internos.
- Comparar las capturas móvil y escritorio con el mismo contenido realista.
