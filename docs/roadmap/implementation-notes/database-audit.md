# Auditoría de base de datos

La base de datos cubre tenants, usuarios, roles, conversaciones, runs,
eventos, acciones, citas, auditoría y corpus. Las migraciones incluyen RLS,
índices, restricciones de concurrencia y seeds reproducibles.

## Pendientes

- Paridad completa entre snapshot offline y almacenamiento persistente.
- Índices y consultas analíticas para métricas administrativas.
- Persistencia durable de checkpoints y eventos de workflow.
- Pruebas de backup, recuperación, aislamiento y cargas representativas.
