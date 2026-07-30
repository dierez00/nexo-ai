# Mocks

## Objetivo

Almacena respuestas sintéticas de Twilio, modelos y sistemas institucionales.

No contiene tokens, teléfonos reales ni respuestas copiadas de producción. Los payloads conservan el mismo schema que el adapter real e incluyen escenarios success, timeout, conflict y malformed.

Convención: `proveedor/capacidad/escenario.v1.json`; IDs y datos claramente sintéticos.

Responsable: Daher; Dani mantiene Twilio/adapters y Diego tools/modelos.

Dependencias permitidas: `integrations`, `tests`, MCP y modelos falsos consumen los fixtures. Ejemplos: `twilio/inbound_text.v1.json` y `appointments/conflict.v1.json`.

Tareas: fixtures de dos recorridos MVP, webhook duplicado, slot competido y provider down. Terminado cuando E2E puede correr sin red y contract tests aceptan mock/adapter por igual.
