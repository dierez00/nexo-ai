# 0005 — MCP como frontera de capacidades y aislamiento de escrituras

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Estado:** accepted
- **Revisión:** adapters, red, auditoría, idempotencia y citas
- **Tarea:** `DIE-F0-005`

## Contexto

Las acciones con efecto real —reservar una cita, registrar una solicitud,
registrar una vacuna— son el punto donde un error deja de ser una respuesta
incorrecta y pasa a ser un daño. Necesitan una frontera explícita, no una
función más que un agente pueda llamar.

## Opciones consideradas

| Opción | A favor | En contra |
|---|---|---|
| **MCP con frontera de proceso/protocolo** | Estándar, schemas tipados, interoperable; la frontera es física, no una convención | Un proceso más que arrancar y observar |
| Funciones Python invocadas desde el agente | Simple y rápido | El aislamiento depende de la disciplina de quien escribe el agente |
| RPC interno propio | Control total | Reinventar descubrimiento, versionado y schemas sin ganar nada |

## Decisión

**MCP conserva una frontera de proceso/protocolo**, incluso dentro del monolito
modular. Sobre ella, cinco reglas de aislamiento de escrituras:

1. **Solo el agente transaccional puede solicitar tools de escritura.** El
   contrato `AgentResult` lo rechaza para cualquier otro agente; no es una
   comprobación en tiempo de ejecución que alguien pueda olvidar.
2. **Una tool de escritura no puede registrarse sin confirmación e
   idempotencia.** `ToolMetadata` rechaza `mode=write` sin
   `requires_confirmation` y `requires_idempotency_key`, y con
   `max_attempts != 1`.
3. **Descubrimiento, propuesta, confirmación y ejecución están separados.** El
   supervisor filtra la lista antes de mostrarla al modelo; el executor
   **revalida** por su cuenta. Ninguna capa confía en la otra, y ninguna confía
   en el agente.
4. **Sin identificador verificable no hay éxito.** Un resultado de escritura sin
   folio, UUID o equivalente se reporta como `partial`, nunca como éxito
   inferido.
5. **Una escritura con outcome desconocido no se reintenta jamás.**
   `UNKNOWN_OUTCOME` no puede marcarse reintentable ni aparecer en un `retry_on`
   de configuración; ambas cosas detienen la validación.

Los adapters mock conservan exactamente el wire shape del adapter real futuro,
de modo que sustituirlos no cambie ni un contrato ni una prueba.

## Consecuencias

**A favor**

- Una escritura sin confirmación no es difícil: es imposible de construir.
- Las integraciones institucionales avanzan como mocks sin bloquear el resto.
- El MCP Mapper (Fase 3) tiene dónde publicarse sin ampliar permisos.

**En contra**

- Una frontera de proceso añade latencia y un componente que observar.
- Las reglas viven en los contratos, así que relajarlas exige una versión nueva
  de contratos. Es el efecto buscado, pero encarece un cambio legítimo.

## Evidencia

- `contracts/src/nexo_contracts/tools.py`, `mcp/src/nexo_mcp/ports.py`
- `mcp/tests/test_executor.py` — permiso revalidado, versión inexistente
  denegada, confirmación repetida sin segunda escritura, outcome desconocido no
  reintentable.
- `contracts/tests/test_invariants.py` — un agente no transaccional no puede
  proponer una escritura.

## Criterio de reevaluación

Se reabre si el costo de la frontera de proceso resulta injustificable con el
volumen real, o si MCP evoluciona de forma incompatible con nuestros schemas.
