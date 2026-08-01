# 0007 — Ledger de idempotencia y eventos SSE vivos en MVP

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Estado:** accepted

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
- Las migraciones e índices, el `EventSinkPort` del grafo y la frontera HTTP/SSE
  deben conservar el mismo contrato y secuencia de eventos.
