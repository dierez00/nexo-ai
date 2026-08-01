# Notas de implementación — Fase 2

La Fase 2 introdujo un catálogo central, snapshots de cinco dominios, fixtures
de workflow, evaluación Core y validaciones adversariales para documentos,
tools y superficies A2UI.

## Hallazgos consolidados

- Las proyecciones administrativas deben derivarse del catálogo real.
- El workflow debe reconstruirse desde eventos y no desde una maqueta estática.
- Cada dominio necesita lifecycle documental activo, vencido, sustituido y
  adversarial.
- Las respuestas hostiles de una tool no pueden convertirse en hechos.
- Las acciones pendientes deben resolverse por intent y catálogo, no por una
  rama fija de dominio.

## Pendientes

Paridad con la persistencia, replays conectados al stream real, consultas
analíticas autorizadas, cobertura frontend y dependencia opcional documentada
para pruebas de PostgreSQL.
