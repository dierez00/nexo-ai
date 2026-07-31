# 0007 — Ledger de idempotencia y eventos SSE vivos en MVP

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Decisores:** Dani, Daher y Diego

## Decisión

Las escrituras HTTP usan un ledger compartido por `tenant_id`, operación y
`Idempotency-Key`. La clave se reserva y confirma antes de invocar un proveedor
o crear el recurso. El ledger compara el hash canónico del request, reproduce
resultados conocidos y deja `UNKNOWN_OUTCOME` sin reintento automático cuando el
efecto externo no se puede verificar.

Los runs MVP se ejecutan como tareas administradas dentro de la API. Cada evento
se persiste al emitirse con `event_id` y `sequence` 1-indexada por run. SSE usa
esa secuencia para replay por `Last-Event-ID`, polling de 500 ms y keepalive de
15 s.

## Consecuencias

- Acciones y holds no duplican efectos por reintentos concurrentes dentro de
  Nexo; los adapters reciben la clave estable para propagarla al proveedor.
- Una caída de proceso puede convertir una reserva en `unknown`; un operador
  debe reconciliarla. No se promete ejecución durable hasta introducir cola y
  workers separados.
- Daher mantiene la migración y los índices; Diego integra el `EventSinkPort`
  del grafo real; Dani mantiene la frontera HTTP, SSE y el run manager.
