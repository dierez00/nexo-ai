# Web: portal y administración

## Objetivo

Entregar `/portal` y `/admin` desde una sola aplicación Next.js, con chat, A2UI, workflow y dashboards accesibles.

## Estado actual

Interfaz conectada al backend FastAPI para auth, chat/SSE y métricas admin básicas.
Algunas vistas conservan fixtures como fallback visual mientras se completan los
flujos operativos.

| Ruta                                                                                  | Estado                                                                        |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `/login`                                                                              | implementada — login proxy vía FastAPI/Supabase Auth                          |
| `/`                                                                                   | landing con los tres canales                                                  |
| `/portal`, `/portal/chat`, `/portal/tramite`, `/portal/citas`, `/portal/seguimiento`  | protegidas; chat conectado a conversaciones/runs/SSE reales                   |
| `/admin`, `/admin/runs`, `/admin/workflow`, `/admin/catalogo`, `/admin/integraciones` | protegidas por rol admin; dashboard consume métricas/catálogo/config          |
| `/agente-voz`                                                                         | **implementada** — llamada real vía ElevenLabs (`@elevenlabs/client`, WebRTC) |
| `/admin/a2ui-lab`                                                                     | **implementada** — renderer A2UI sobre superficies reales de `nexo-a2ui`      |

`/portal/chat` es la vista de referencia: expone los 12 estados del chat (vacío, cargando,
error, sin resultados, requisitos, agendar, confirmada, completado, seguimiento…) desde un
selector, para diseñar contra loading/empty/error/partial antes de tener backend.

Fixtures en `src/features/chat/chat-mock.ts` y `src/lib/mock.ts`. Se mantienen
para fallback visual y laboratorios mientras los endpoints operativos maduran.

## Renderer A2UI

`src/features/a2ui/` dibuja las superficies del catálogo ciudadano
`urn:nexo-ia:a2ui:catalog:citizen:v1`. Las superficies **no** las genera un modelo: el
builder de `a2ui/` es determinista y las arma desde plantillas y hechos verificados
(ADR 0006). El frontend solo renderiza y vuelve a validar.

| Pieza                          | Qué hace                                                                                                                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `guard.ts`                     | Rechaza antes de dibujar: catálogo, allowlist de componentes y propiedades, claves `on*`, HTML, URLs no https, ids duplicados, `root`, hijos, ciclos y acciones no declaradas |
| `processor.ts`                 | Lifecycle: `createSurface` primero, ids inmutables, descarta la instancia ante error                                                                                          |
| `pointer.ts`                   | JSON Pointer (RFC 6901) para los bindings `{path}`                                                                                                                            |
| `registry.tsx`                 | Los 10 componentes del catálogo, renderizados con las cards del chat                                                                                                          |
| `Surface.tsx` / `Fallback.tsx` | Render desde `root` y fallback seguro sin revelar el payload                                                                                                                  |

Los fixtures salen del builder real:

```bash
# desde la raíz del repo
uv run --python 3.12 --with-editable ./contracts --with-editable ./a2ui \
  python a2ui/scripts/export_fixtures.py
npm run check:catalog   # la copia del catálogo no se desincronizó de a2ui/
```

Genera 4 superficies válidas y 15 hostiles en `public/fixtures/a2ui/` — una por cada regla
que el guard debe hacer cumplir. `/admin/a2ui-lab` las recorre y mide la línea de tiempo
hasta la primera superficie pintada.

### Ejecutar

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_ELEVENLABS_AGENT_ID es necesario para /agente-voz
npm run dev
```

Variables web:

```bash
NEXT_PUBLIC_NEXO_API_URL=http://localhost:8000
NEXT_PUBLIC_ELEVENLABS_AGENT_ID=
```

La sesión del browser se guarda en `localStorage` como `nexo.auth.v1`; el
frontend manda `Authorization: Bearer <access_token>` a FastAPI y pasa el token
en `?access_token=` únicamente para SSE, porque `EventSource` no permite headers.

### Stack

Next.js 16 (App Router) · React 19 · Tailwind v4 (CSS-first: el design system vive en
`src/app/globals.css`, sin `tailwind.config.ts`) · shadcn/ui a demanda · TanStack Query
para la futura capa de datos.

## Debe contener

Rutas, componentes, sesión, cliente OpenAPI/SSE, renderer A2UI, workflow y pruebas de interfaz.

## No debe contener

Acceso directo a PostgreSQL, secretos, prompts, autorización real ni ejecución de tools. Ocultar un botón no reemplaza un permiso server-side.

## Convenciones

- TypeScript estricto; componentes `PascalCase`; hooks `useX`.
- Features por capacidad, no por página.
- Estados loading/empty/error/partial explícitos.
- Accesibilidad con teclado, labels y contraste como baseline.

## Dependencias y responsables

Depende de `contracts` y la API. Cris es responsable; Dani apoya auth/API y Diego A2UI/eventos.

## Archivos y tareas iniciales

Ejemplos: `src/features/chat`, `src/features/a2ui`, `src/features/workflow`, `src/lib/api`. Implementar shell, login, streaming, catálogo MVP, citas, admin y Playwright.

## Terminado

Los dos recorridos MVP funcionan en navegador; los roles protegen rutas; una surface inválida degrada sin ejecutar código y los tests de accesibilidad/contrato pasan.
