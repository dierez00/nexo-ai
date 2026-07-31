# Integración con Supabase local

Estas pruebas se ejecutan en CI después de `supabase start` y `supabase db reset`.
El smoke actual valida que las migraciones del ledger de idempotencia y la
secuencia SSE se apliquen junto con el esquema completo. Los casos concurrentes
de actions/holds se añaden aquí al conectar la API contra el proyecto local.
