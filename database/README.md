# Base de datos

## Objetivo

Definir persistencia relacional/vectorial, migraciones, seeds y garantías de integridad.

## Debe contener

Alembic, extensiones, tablas, constraints, índices, repositorios y queries administrativas aprobadas.

## No debe contener

Lógica LLM, credenciales, dumps con PII ni cambios manuales sin migración.

## Convenciones

`snake_case`, IDs opacos, `timestamptz`, dinero en minor units, `institution_id`, migraciones expand/contract y seeds idempotentes.

## Dependencias y responsable

PostgreSQL/pgvector y contratos de persistencia. Responsable: Daher.

## Ejemplos y tareas

`migrations/versions`, `seeds/demo.py`, `queries/dashboard.sql`. Crear ERD, identidad/RBAC, catálogo/RAG, runs, citas GiST, auditoría e índices.

## Terminado

Migrar desde cero y actualizar funciona; dos reservas concurrentes no se solapan; seeds no duplican y backup/restore tiene smoke test.
