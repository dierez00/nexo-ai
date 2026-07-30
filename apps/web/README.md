# Web: portal y administración

## Objetivo

Entregar `/portal` y `/admin` desde una sola aplicación Next.js, con chat, A2UI, workflow y dashboards accesibles.

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
