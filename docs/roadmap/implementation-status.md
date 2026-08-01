# Estado de implementación

Este snapshot resume el estado observable en el código y las pruebas. Las
etiquetas distinguen funcionamiento real, dobles reproducibles y deuda.

| Área | Estado | Evidencia |
| --- | --- | --- |
| Contratos, OpenAPI, JSON Schema y eventos | Implementado | `contracts/` |
| API FastAPI, auth, conversaciones, SSE, citas y acciones | Implementado | `backend/` |
| Portal y administración web | Implementado con fixtures de fallback | `apps/web/` |
| Orquestación y agentes transversales | Implementado | `orchestration/`, `agents/` |
| RAG, corpus y evaluación offline | Implementado | `rag/`, `data/`, `evaluations/` |
| MCP y herramientas | Implementado con adapters mock | `mcp/`, `integrations/` |
| A2UI ciudadano v1 | Implementado y congelado | `a2ui/` |
| Base de datos multi-tenant y migraciones | Implementado | `database/`, `supabase/` |
| Integraciones institucionales | Pendiente de contratos externos | `integrations/` |
| Worker durable y ejecución distribuida | Pendiente | Roadmap Pro |
| Cinco recorridos completos de dominio | Parcial | Roadmap Core |
| MCP Mapper, routing productivo y formularios dinámicos | Pendiente | Roadmap Pro |
| Paralelismo, mini-RAGs y judge avanzado | Pendiente | Roadmap Extremo |

## Próximas prioridades

1. Verificar paridad continua entre contratos, API, frontend y eventos.
2. Cubrir con pruebas de navegador los estados de portal y administración.
3. Completar los recorridos Core sin presentar fixtures como producción.
4. Separar los runs activos del proceso HTTP mediante worker durable.
5. Establecer métricas comparables de fidelidad, coste, latencia y seguridad.
