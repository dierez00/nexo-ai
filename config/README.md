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

## Estado tras Fase 0

Cinco archivos validados al arranque contra los schemas de
`nexo_contracts.config`. Una configuración inválida detiene el proceso con
ruta, campo y motivo antes de aceptar el primer run.

| Archivo | Schema | Default seguro |
|---|---|---|
| `model_router.yaml` | `ModelRouterConfig` | Proveedor no declarado detiene el arranque |
| `tool_registry.yaml` | `ToolRegistryConfig` | `enabled: false`; registrar no habilita |
| `permissions.yaml` | `PermissionsConfig` | `default_allow: false`; escrituras tool por tool |
| `catalogs.yaml` | `CatalogsConfig` | `catalog_id` inmutable por versión |
| `policies.yaml` | `PoliciesConfig` | Sin reintento automático de escrituras |

`policies.version` se propaga a cada evento y a cada reporte de evaluación.
Los secretos se referencian con `secret://…` y se resuelven fuera del repositorio.
