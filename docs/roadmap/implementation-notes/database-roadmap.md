# Roadmap de persistencia

La persistencia debe evolucionar conservando compatibilidad, aislamiento por
tenant y trazabilidad.

1. Mantener migraciones expand/contract y seeds idempotentes.
2. Verificar índices de citas, eventos y corpus con pruebas de integración.
3. Añadir consultas agregadas para métricas autorizadas.
4. Persistir checkpoints y replays de forma durable.
5. Validar backup, restore y migraciones en un entorno reproducible.
