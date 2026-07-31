# Convenciones transversales de Nexo IA

> **Tareas:** `DIE-F0-007`, `DIE-F0-008`, `DIE-F0-009`, `DIE-F0-010`.
> **Fecha:** 2026-07-30. **Mantiene:** Diego. **Aprueban:** Dani, Daher, Cris.
>
> Este documento es la referencia normativa. Cuando una convención está
> verificada por código o pruebas, se indica dónde: una regla que solo vive en
> prosa termina incumpliéndose.

## 1. Compatibilidad de contratos (`DIE-F0-007`)

Dentro de una versión mayor (`v1`) solo se admiten **cambios aditivos**:

- añadir un campo opcional con default;
- añadir un miembro nuevo a un enum;
- relajar una restricción (ampliar un rango, subir un `max_length`);
- añadir un contrato nuevo al registro.

Exigen **versión nueva** (`v2`):

- eliminar o renombrar un campo;
- volver obligatorio un campo opcional;
- estrechar un tipo o un rango;
- eliminar o renombrar un miembro de enum;
- cambiar el significado de un campo conservando su nombre.

Una versión nueva no borra la anterior: coexisten hasta que todos los
consumidores migren. El proceso de aprobación está en
[`contracts/CHANGELOG.md`](../../contracts/CHANGELOG.md).

**Verificado por:** `contracts/tests/test_schema_export.py` — los artefactos
publicados no pueden desincronizarse del modelo.

## 2. Identificadores (`DIE-F0-008`)

Formato: `<prefijo>_<cuerpo>`. El cuerpo es **opaco**: no transporta significado
ni datos personales, y ningún consumidor debe parsearlo.

| Prefijo | Entidad | Prefijo | Entidad |
|---|---|---|---|
| `usr_` | usuario | `fact_` | hecho |
| `inst_` | institución | `src_` | fuente documental |
| `conv_` | conversación | `doc_` | documento |
| `msg_` | mensaje | `frag_` | fragmento citable |
| `run_` | ejecución | `chunk_` | fragmento indexado |
| `trace_` | traza distribuida | `tool_` | tool registrada |
| `task_` | tarea de agente | `tc_` | invocación de tool |
| `evt_` | evento | `mdl_` | invocación de modelo |
| `chk_` | checkpoint | `surf_` | superficie A2UI |
| `act_` | acción confirmable | `skill_` | skill operativa |
| `apt_` | cita | `eval_` | evaluación |
| `contra_` | contradicción | `intg_` | integración del Mapper |

La `idempotency_key` es un espacio aparte: la genera el cliente o el backend y
es un UUID, no un ID con prefijo.

**Verificado por:** `contracts/src/nexo_contracts/ids.py` — un prefijo no
registrado y un ID con forma de teléfono o correo fallan en validación.

## 3. Tiempo, montos y puntajes

- **Fechas y horas:** ISO 8601 en **UTC**, siempre con zona horaria. Un
  `datetime` ingenuo se rechaza; no se asume la zona del servidor.
- **Vigencias documentales:** fecha civil sin hora (`valid_from`, `valid_to`).
  `valid_to` nulo significa vigencia abierta.
- **Montos:** `{"amount_minor": 125000, "currency": "MXN"}`. Nunca en flotante.
  Se suman con código sobre `amount_minor`; sumar montos en un prompt está
  prohibido. Mezclar monedas es un error, no una conversión implícita.
- **Puntajes y confianzas:** acotados a `[0, 1]`.
- **Duraciones:** milisegundos enteros, con tope de una hora para detectar
  errores de unidad.

**Verificado por:** `contracts/src/nexo_contracts/primitives.py` y
`contracts/tests/test_invariants.py`.

## 4. Wire format

- JSON en `snake_case`, UTF-8.
- Propiedades desconocidas **se rechazan** (`extra="forbid"` transversal). Un
  campo no declarado es un error de contrato, no un dato que se ignora.
- Cada respuesta incluye o propaga `trace_id`.
- **Única excepción:** los mensajes A2UI v0.9.1 usan `camelCase`
  (`createSurface`, `surfaceId`, `catalogId`) porque así lo define el protocolo.
  La excepción está acotada al paquete `nexo_contracts.a2ui`; ver
  [ADR 0006](../adr/0006-a2ui-091-catalogo-cerrado-y-fallback.md).

## 5. Nombres de tools y namespaces

Formato: `dominio.verbo_objeto`, todo en `snake_case`.

| Dominio (namespace) | Prefijo de tool |
|---|---|
| `vehiculos` | `vehiculos` |
| `ayuntamiento_empresas` | `ayuntamiento` |
| `registro_civil` | `registro_civil` |
| `salud` | `salud` |
| `ganaderia` | `ganaderia` |

`ayuntamiento_empresas` es el único caso en que el prefijo difiere del slug del
dominio; se conserva el prefijo corto porque así están nombradas las tools del
MVP en el plan. La correspondencia se valida en `ToolMetadata`: declarar un
dominio y usar otro prefijo falla.

## 6. Errores

Todo fallo que cruza una frontera se representa igual: código estable,
reintentabilidad explícita, certeza sobre el efecto y detalles seguros. Ningún
consumidor decide leyendo el texto del mensaje.

| Código | HTTP | Uso |
|---|---:|---|
| `VALIDATION_ERROR` | 400 | Payload o schema inválido |
| `CONTRACT_INVALID` | 400 | Contrato incompatible entre módulos |
| `AUTHENTICATION_REQUIRED` | 401 | Sesión ausente o inválida |
| `PERMISSION_DENIED` | 403 | Rol, dominio u operación no autorizada |
| `RESOURCE_NOT_FOUND` / `TOOL_NOT_FOUND` | 404 | ID no visible o inexistente |
| `APPOINTMENT_CONFLICT` / `VERSION_CONFLICT` | 409 | Carrera o versión obsoleta |
| `ACTION_CONFIRMATION_REQUIRED` | 422 | Falta consentimiento o dato obligatorio |
| `RATE_LIMITED` / `BUDGET_EXCEEDED` | 429 | Límite de proveedor, usuario o costo |
| `PROVIDER_ERROR` / `MODEL_OUTPUT_INVALID` | 502 | Integración o salida de modelo falló |
| `MODEL_UNAVAILABLE` / `CONFIGURATION_INVALID` / `UNKNOWN_OUTCOME` | 503 | Fallback agotado o efecto incierto |
| `TOOL_TIMEOUT` / `RUN_TIMEOUT` | 504 | Deadline agotado |
| `RUN_CANCELLED` | 499 | Cancelado por el cliente |

**`UNKNOWN_OUTCOME` es el caso crítico.** Significa que no sabemos si la
operación tuvo efecto. Nunca es reintentable, nunca aparece en un `retry_on` de
configuración y siempre degrada el run a `partial`. Ambas prohibiciones fallan
en validación, no en revisión de código.

## 7. Política de PII (`DIE-F0-009`)

Aplica a prompts, eventos, datasets, recordings, reportes y fixtures.

**Nunca se versiona ni se transporta**

- nombres, teléfonos, correos, domicilios, CURP, RFC, NSS ni placas reales;
- credenciales, tokens, cookies, identificadores de sesión;
- contenido copiado de producción.

**Cómo se sustituye**

- identidades → IDs opacos (`usr_demo`);
- datos de contacto → referencias opacas (`pii_ref:phone_01`);
- documentos → contenido sintético marcado `is_synthetic: true`;
- secretos → referencias `secret://…` resueltas fuera del repositorio.

**Cómo se hace cumplir**

- `SafePayload` rechaza claves con aspecto de secreto o de PII directa en
  eventos, parámetros de tools, metadata y auditoría;
- una prueba de seguridad recorre todos los fixtures publicados buscando
  contenido prohibido;
- los ejemplos deliberadamente inválidos viven en `contracts/examples/invalid/`
  y quedan excluidos de esa prueba, porque su propósito es demostrar el rechazo.

**Límite conocido:** es una barrera sintáctica. No detecta un secreto guardado
bajo un nombre inocuo. Su función es que el caso descuidado y frecuente falle en
validación, no en producción.

## 8. Qué detiene el run, qué lo degrada y qué admite fallback (`DIE-F0-010`)

Las tres categorías son **disjuntas**: la reacción ante un error nunca es
ambigua. Están codificadas en `config/policies.yaml`, no solo aquí, para que el
grafo consulte la regla en vez de que cada nodo improvise.

| Categoría | Códigos | Comportamiento |
|---|---|---|
| **Detiene el run** (`halt_on`) | `CONFIGURATION_INVALID`, `AUTHENTICATION_REQUIRED`, `PERMISSION_DENIED`, `CONTRACT_INVALID`, `RUN_CANCELLED` | El run termina en `failed`. No se intenta nada más: seguir sería operar sin autorización o sin contrato válido. |
| **Degrada a parcial** (`partial_on`) | `UNKNOWN_OUTCOME`, `RUN_TIMEOUT`, `BUDGET_EXCEEDED`, `TOOL_TIMEOUT` | El run termina en `partial` con warning y traza. Se entrega lo verificado; nunca se infiere un éxito. |
| **Permite fallback** (`fallback_on`) | `MODEL_UNAVAILABLE`, `MODEL_OUTPUT_INVALID`, `RATE_LIMITED`, `PROVIDER_ERROR` | Se intenta el alias de respaldo o la plantilla determinista. Si el fallback también falla, se aplica la regla anterior. |

Reglas que ninguna categoría puede violar:

1. Una escritura con outcome desconocido **jamás** se reintenta.
2. Un fact crítico sin evidencia bloquea cualquier escritura que dependa de él.
3. Una contradicción crítica sin resolver bloquea la escritura, aunque el resto
   del run sea correcto.
4. El redactor nunca compensa un fallo inventando información: si no hay
   `VerifiedFacts`, no hay claim.

**Verificado por:** `orchestration/tests/test_configuration.py` (categorías
disjuntas, sin reintento de escrituras) y `orchestration/tests/test_graph.py`
(el deadline degrada a `partial`, un run fallido no se finaliza como exitoso).

## 9. Glosario

| Término | Significado preciso |
|---|---|
| **Claim crítico** | Afirmación sobre requisitos, costos, ubicación, vigencia, dependencias o resultado de una acción. Exige citación activa. |
| **CandidateFact** | Hecho propuesto por un agente, aún sin verificar. |
| **VerifiedFact** | Hecho tras el verificador, con `accepted`, `rejected` o `uncertain` y motivo estable. |
| **VerifiedFacts** | Snapshot inmutable. Es el universo completo del que puede hablar el redactor. |
| **Deducción** | Dato inferido, no afirmado ni leído de una fuente. No alimenta escrituras sin confirmación. |
| **Outcome desconocido** | No sabemos si la operación tuvo efecto. Nunca se reintenta. |
| **Folio verificable** | Identificador devuelto por el sistema destino. Sin él no hay éxito. |
| **Perfil offline** | Ejecución completa sin red, proveedor ni credenciales, con modelo y tools falsos. |
| **Corpus version** | Instantánea versionada del corpus de un dominio. Viaja en cada citación. |
| **Catálogo A2UI** | Allowlist exhaustiva de componentes. Inmutable por versión. |
| **Fallback de canal** | Representación en texto plano cuando la superficie no puede renderizarse. |
