# Web: portal y administración

## Objetivo

Entregar `/portal` y `/admin` desde una sola aplicación Next.js, con chat, A2UI, workflow y dashboards accesibles.

## Estado actual

Interfaz completa con **fixtures estáticos** (Fase 0): no hay API, SSE ni auth todavía.
La única capacidad conectada a un servicio real es el agente de voz.

| Ruta                                                                                  | Estado                                                                        |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `/`                                                                                   | mock — landing con los tres canales                                           |
| `/portal`, `/portal/chat`, `/portal/tramite`, `/portal/citas`, `/portal/seguimiento`  | mock                                                                          |
| `/admin`, `/admin/runs`, `/admin/workflow`, `/admin/catalogo`, `/admin/integraciones` | mock                                                                          |
| `/agente-voz`                                                                         | **implementada** — llamada real vía ElevenLabs (`@elevenlabs/client`, WebRTC) |

`/portal/chat` es la vista de referencia: expone los 11 estados del chat (vacío, cargando,
error, sin resultados, requisitos, agendar, confirmada, completado, seguimiento…) desde un
selector, para diseñar contra loading/empty/error/partial antes de tener backend.

Fixtures en `src/features/chat/chat-mock.ts` y `src/lib/mock.ts`. Al conectar la API real,
esos dos archivos son los únicos puntos a reemplazar.

### Ejecutar

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_ELEVENLABS_AGENT_ID es necesario para /agente-voz
npm run dev
```

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
