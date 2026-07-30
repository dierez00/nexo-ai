# Infraestructura

## Objetivo

Definir imágenes, Compose, Railway, topología futura y runbooks.

## Debe contener

Dockerfiles, healthchecks, redes, volúmenes, IaC, deployment y recuperación.

## No debe contener

Secretos, lógica de aplicación o recursos manuales no documentados.

## Convenciones

Imágenes fijadas, inmutables y non-root; health/readiness; configuración por entorno; storage explícitamente persistente o efímero.

## Dependencias y responsable

Depende de entrypoints públicos y variables documentadas. Responsable: Dani.

## Ejemplos y tareas

`docker/api.Dockerfile`, `railway/README.md`, `production/topology.md`. Crear Compose, perfiles, Railway, backup y rollback.

## Terminado

Un entorno limpio arranca y pasa smoke/health; puede destruirse/recrearse sin pérdida no documentada.
