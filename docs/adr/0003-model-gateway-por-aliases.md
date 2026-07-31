# 0003 — Model gateway por aliases y adapters

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Decisor:** Diego
- **Revisan:** Dani (adapters y telemetría)
- **Tarea:** `DIE-F0-003`

## Contexto

Los proveedores de modelos cambian de precio, de disponibilidad y de contrato
con más frecuencia que nuestro producto. Si un agente importa el SDK de un
proveedor, cambiarlo obliga a tocar código de dominio, reescribir pruebas y
revalidar guardrails.

## Opciones consideradas

| Opción | A favor | En contra |
|---|---|---|
| **Gateway propio con aliases** | Routing controlado, telemetría uniforme, cero acoplamiento en agentes | Hay que construir y mantener el gateway |
| SDK del proveedor directo en cada agente | Cero capa intermedia | Acopla dominio a proveedor; imposibilita routing por política, salud y costo |
| LiteLLM Proxy | Multi-proveedor resuelto | Otro proceso que operar; su modelo de políticas no cubre riesgo ni privacidad como los necesitamos |

## Decisión

Un **gateway propio detrás de `ChatModelPort`**, con estas reglas:

1. **Los agentes piden un alias**, nunca un modelo. `high_accuracy`,
   `structured_small`, `offline_fake`. El alias se resuelve en
   `config/model_router.yaml`.
2. **La configuración no contiene credenciales**, solo referencias
   `secret://…` que se resuelven fuera del repositorio.
3. **El conjunto de proveedores es cerrado.** Un alias que apunte a un proveedor
   ausente de `allowed_providers` detiene el arranque.
4. **Todo error se normaliza.** El puerto lanza `ModelPortError` con un
   `NormalizedError` de código estable; ninguna excepción de SDK cruza la
   frontera.
5. **La solicitud declara `purpose`**, una clave estable del punto de invocación.
   Los dobles responden por esa clave y no haciendo matching sobre el texto del
   prompt, que es frágil y desincentiva mejorarlo.
6. **El perfil offline es obligatorio.** `offline_alias` debe existir, estar
   habilitado y no requerir credenciales: la demo y la suite completa corren sin
   red.

El router automático por complejidad, salud y presupuesto es Fase 3 (F3.1); el
routing por carga, Fase 4 (F4.7). Fase 0 congela el contrato para que ninguna de
las dos obligue a cambiarlo.

## Consecuencias

**A favor**

- Cambiar de proveedor es editar YAML.
- Costo, tokens, latencia y motivo de fallback se registran en un solo lugar.
- La demo offline no es un modo degradado: es un alias más.

**En contra**

- El gateway es código propio que hay que probar y mantener.
- Un alias mal configurado es un fallo de arranque, no de ejecución. Es
  deliberado, pero exige que el error diga ruta, campo y motivo.

## Evidencia

- `contracts/src/nexo_contracts/model_gateway.py`
- `config/model_router.yaml`
- `orchestration/tests/test_configuration.py` — proveedor desconocido, alias
  colgante y alias offline inexistente detienen el arranque.

## Criterio de reevaluación

Se reabre si el número de proveedores hace que mantener adapters cueste más que
operar un proxy externo, o si aparece un estándar de routing que cubra riesgo,
privacidad y presupuesto sin perder control.
