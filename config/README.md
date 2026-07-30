# Configuración

## Objetivo

Versionar configuración no secreta de aliases, tools, permisos, catálogos y policies.

## Debe contener

YAML/JSON validado con defaults seguros y ejemplos por entorno.

## No debe contener

API keys, passwords, tokens, URLs privadas ni valores exclusivos de producción.

## Convenciones

Todo archivo tiene schema/versión; overrides mediante variables; configuración inválida detiene el arranque con error accionable.

## Dependencias y responsables

`contracts` define schemas. Dani y Diego comparten responsabilidad.

## Ejemplos y tareas

`model_router.yaml`, `tool_registry.yaml`, `permissions.yaml`. Crear schemas, ejemplos y validación startup.

## Terminado

Policies pueden revisarse en PR, secretos se resuelven fuera del repo y los defaults no permiten escrituras peligrosas.
