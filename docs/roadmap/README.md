# Roadmap y evolución

El roadmap organiza el trabajo por capacidades del producto y no por personas.
El estado se contrasta con el código, los contratos y las pruebas existentes.

## Fases

| Fase | Objetivo | Estado |
| --- | --- | --- |
| MVP | Portal, API, autenticación, dos recorridos E2E, agentes, RAG, MCP mock y A2UI | Implementado con deuda técnica |
| Core | Cinco dominios, catálogo central, workflow reproducible, evaluación y administración | Parcial |
| Pro | Voz, integraciones reales, MCP Mapper, formularios dinámicos y routing productivo | Pendiente/parcial |
| Extremo | Paralelismo, mini-RAGs, personalización, judge y actualización controlada | Pendiente |

## Prioridades actuales

1. Mantener la paridad entre contratos, API, frontend y eventos.
2. Completar la base de pruebas y los recorridos de los cinco dominios.
3. Separar la ejecución de runs en un worker o cola durable.
4. Sustituir adapters mock por integraciones verificadas cuando existan contratos
   externos autorizados.
5. Medir latencia, coste, fidelidad de citas, seguridad y accesibilidad.

## Notas de implementación

- [Estado consolidado](implementation-status.md)
- [Hallazgos de Fase 0](implementation-notes/phase-0-findings.md)
- [Hallazgos de Fase 1](implementation-notes/phase-1-findings.md)
- [Hallazgos de Fase 2](implementation-notes/phase-2-findings.md)
- [Capacidades de frontend](implementation-notes/frontend-capabilities.md)
- [Servicios de plataforma](implementation-notes/platform-services.md)
- [Sistema de agentes](implementation-notes/agent-system-capabilities.md)
- [Auditoría de base de datos](implementation-notes/database-audit.md)
