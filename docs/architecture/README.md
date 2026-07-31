# Documentos de arquitectura

## Objetivo

Desglosar vistas de arquitectura que requieran más detalle que el documento maestro.

## Contenido permitido

Contexto, contenedores, componentes, secuencias, modelo de datos, seguridad, despliegue y decisiones de escalamiento.

## Fuera de alcance

Roadmaps personales, secretos y documentación de API que pertenezca a `contracts`.

## Convenciones

Diagramas Mermaid versionables, leyenda, fecha y enlace a ADR relacionada. Describir estado actual y objetivo por separado.

Responsable: equipo; Dani/Diego revisan fronteras runtime y Daher persistencia.

## Archivos, tareas y terminado

Dependencias permitidas: contratos, ADR y diagramas del sistema; el runtime no depende de esta carpeta.
- [database_schema.md](./database_schema.md): Esquema completo de la base de datos (PostgreSQL/Supabase), migraciones, RLS, índices, funciones RPC y diagrama ERD.
- [institutional_adapters_inventory.md](./institutional_adapters_inventory.md): Inventario de todos los adapters/dobles falsos actuales (tools mock institucionales y proveedores de infraestructura) y qué comportamiento simula cada uno.

Ejemplos: `overview.md`, `database_schema.md`, `security.md`. Crear solo cuando el detalle no quepa en `Nexo_IA_Arquitectura_y_Plan.md`. Terminado cuando coincide con código, contratos y despliegue.
