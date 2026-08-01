# Documentación

La documentación describe el producto, sus fronteras técnicas, el estado
actual y la evolución prevista. Los documentos deben reflejar el código y los
contratos publicados, no planes privados ni asignaciones individuales.

## Índice

| Sección | Propósito |
| --- | --- |
| [`product/`](product/) | Problema, propuesta de valor, alcance y casos de uso |
| [`architecture/`](architecture/) | Arquitectura, módulos, contratos y flujos |
| [`adr/`](adr/) | Decisiones técnicas con contexto y consecuencias |
| [`getting-started/`](getting-started/) | Instalación y desarrollo local |
| [`roadmap/`](roadmap/) | Estado, fases, capacidades pendientes y notas de implementación |
| [`runbooks/`](runbooks/) | Operación, despliegue, recuperación e integraciones |
| [`operations/`](operations/) | Guías operativas futuras y criterios de mantenimiento |

Consulta también la [política de código abierto](operations/open-source.md) y
la [licencia MIT](../LICENSE).

## Convenciones

- Usar enlaces relativos y nombres descriptivos en `snake_case` o kebab-case.
- Marcar cada capacidad como implementada, mock, parcial o pendiente.
- Versionar contratos, catálogos, fixtures y decisiones incompatibles.
- No documentar secretos, PII real ni asignaciones personales.
- Actualizar el documento de estado cuando cambien rutas, contratos o fases.

## Puntos de entrada

- [Descripción del producto](product/project-overview.md)
- [Arquitectura técnica](architecture/technical-architecture.md)
- [Estado de implementación](roadmap/implementation-status.md)
- [Roadmap](roadmap/README.md)
- [Desarrollo local](getting-started/local-development.md)
