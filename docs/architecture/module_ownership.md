# Fronteras de módulos

Este documento describe límites técnicos y dependencias. La colaboración se
organiza por interfaces y capacidades, no por personas.

| Capacidad | Módulo principal | Dependencias públicas |
| --- | --- | --- |
| Contratos, eventos y schemas | `contracts` | Ninguna lógica de negocio |
| API, auth, RBAC, SSE y webhooks | `backend` | `contracts`, servicios y adapters |
| Portal, administración y renderer | `apps/web` | API y contratos |
| Estado, grafo y checkpoints lógicos | `orchestration` | Contratos y puertos |
| Agentes y políticas de respuesta | `agents` | Contratos, RAG y MCP |
| Ingesta y retrieval | `rag` | Contratos, corpus y repositorios |
| Herramientas y autorización | `mcp` | Contratos, configuración e integraciones |
| Superficies declarativas | `a2ui` | Contratos y catálogos |
| Migraciones, RLS e índices | `database`, `supabase` | Contratos de persistencia |
| Adaptadores externos | `integrations` | SDKs y contratos |
| Dominios y fuentes | `domains`, `data` | APIs públicas de agentes, RAG y MCP |
| Evaluación y observabilidad | `evaluations`, `observability` | Eventos, fixtures y despliegue |

Las dependencias deben apuntar a contratos o puertos. El acceso incidental a
detalles internos, tablas o SDKs externos queda fuera de las fronteras.
