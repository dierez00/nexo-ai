# Aplicaciones

## Objetivo

Agrupar interfaces desplegables orientadas a personas. Inicialmente solo existirá `web`.

## Contenido permitido

Aplicaciones completas, entrypoints, configuración de build y pruebas específicas de superficie.

## Fuera de alcance

Reglas de agentes, SQL, prompts, secretos y adapters institucionales.

## Convenciones y dependencias

- Nombrar por superficie, no por equipo.
- Consumir backend exclusivamente mediante contratos públicos.
- No importar paquetes Python ni conocer tablas.

Ejemplos: `web/package.json`, `web/src/app/portal` y `web/src/app/admin`.

## Tareas y definición de terminado

Crear workspace, scripts, boundary de variables públicas y smoke test. Cada app debe compilar y documentar healthcheck, configuración y dependencias antes de considerarse terminada.
