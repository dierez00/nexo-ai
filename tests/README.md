# Pruebas

## Objetivo

Organizar pruebas que cruzan límites de módulos y validan la rúbrica.

## Debe contener

Contrato, integración, E2E, seguridad, concurrencia, fallos y fixtures compartidos.

## No debe contener

Unit tests privados de un módulo ni dependencia obligatoria de proveedores reales.

## Convenciones

Arrange/Act/Assert; reloj/IDs controlables; datos sintéticos; tags `unit`, `integration`, `contract`, `e2e`, `eval`.

## Dependencias y mantenimiento

Solo interfaces públicas, Compose de test y mocks. Cada suite debe declarar si
es offline, contractual, E2E o de integración y evitar datos reales.

## Ejemplos y tareas

`contract/test_openapi.py`, `integration/test_appointment_conflict.py`, `e2e/test_vehicle_flow.py`. Cubrir cinco casos, RBAC, routing y fallos.

## Terminado

CI ejecuta suites por nivel, conserva reportes y reproduce una falla con fixtures locales.
