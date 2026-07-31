# 0006 — A2UI v0.9.1, catálogo cerrado y fallback seguro

- **Estado:** accepted — `citizen:v1` congelado
- **Fecha:** 2026-07-30
- **Decisor:** Diego
- **Revisan:** Cris (renderer cerrado); Diego (integración al flujo)
- **Tarea:** `DIE-F0-006`

## Contexto

El producto necesita interfaces que se adapten al trámite y al canal sin que un
modelo genere código. Generar HTML o JavaScript haría imposible validar
permisos, accesibilidad y seguridad antes de renderizar.

## Opciones consideradas

| Opción | A favor | En contra |
|---|---|---|
| **A2UI v0.9.1 con catálogo cerrado** | Declarativo, validable contra schema, sin ejecución de código | Especificación joven; su `camelCase` choca con nuestro wire format |
| HTML/JS generado por el modelo | Máxima flexibilidad | Inaceptable: ejecución arbitraria, imposible de auditar |
| Formato declarativo propio | Ajustado a nuestras necesidades | Sin ecosistema; hay que construir renderer y validador desde cero |

## Decisión

**A2UI v0.9.1** con estas restricciones:

1. **El catálogo es una allowlist exhaustiva.** Un componente ausente de
   `components` no puede aparecer en ninguna superficie válida. `catalog_id` es
   inmutable por versión: cambiar los componentes permitidos exige publicar un
   catálogo nuevo.
2. **Datos y estructura van separados.** Los valores viven en el data model y se
   referencian por binding; el árbol de componentes no los incrusta.
3. **Las acciones son opacas y ligadas a schema, versión y run.** Un componente
   no puede disparar una acción que la superficie no declaró.
4. **Nunca se ejecuta nada.** HTML, JavaScript, SQL o código generado por un
   modelo no tienen representación posible en estos contratos.
5. **Toda superficie tiene fallback.** Si la validación falla, el canal recibe
   texto plano equivalente —lista numerada en WhatsApp, resumen en voz— en lugar
   de nada.
6. **Citizen v1 está congelado desde el 2026-07-30.** El descriptor,
   propiedades, schemas y fixtures entregados quedan ligados a
   `urn:nexo-ia:a2ui:catalog:citizen:v1`. Sus huellas viven en
   `a2ui/catalogs/citizen/v1/freeze.json`; cualquier cambio incompatible
   publica `citizen:v2`.

**Excepción de convención, deliberada y acotada:** A2UI define sus mensajes en
`camelCase` (`createSurface`, `surfaceId`, `catalogId`), mientras el resto del
sistema usa `snake_case`. Se respeta el protocolo tal cual. Los campos Python
siguen en `snake_case` y el alias hace la traducción, acotada al paquete
`nexo_contracts.a2ui`.

## Consecuencias

**A favor**

- Una superficie inválida degrada de forma segura en vez de romper el canal.
- Cris recibe fixtures JSONL válidos e inválidos con la forma exacta del
  protocolo, sin traducción a cargo del renderer.
- El flujo puede integrarse contra una frontera estable; el test de congelación
  detecta drift de catálogo, schemas o fixtures.
- Añadir un componente exige un catálogo nuevo y una decisión revisable en PR.

**En contra**

- A2UI 0.9.x puede cambiar de forma incompatible; el contrato fija la versión y
  rechaza cualquier otra, así que una actualización será explícita y costosa.
- **Límite conocido:** el protocolo aplana las propiedades de cada componente
  junto a `id` y `component`, así que el contrato no puede distinguir una
  propiedad legítima de una mal escrita —qué admite `Checklist` lo sabe el
  catálogo, no el modelo. `A2UIComponent` las absorbe en `properties` y quien
  cierra la allowlist es el validador de catálogo (F1.13, `DIE-F1-104`). Lo que
  el contrato sí impide hoy es que esas propiedades transporten secretos, PII o
  estructuras no serializables.

## Evidencia

- `contracts/src/nexo_contracts/a2ui.py`
- `contracts/tests/test_round_trip.py::test_a2ui_component_absorbs_unknown_properties_by_design`
- `a2ui/catalogs/citizen/v1/catalog.json`
- `a2ui/catalogs/citizen/v1/freeze.json`
- `a2ui/fixtures/citizen/v1/`
- `a2ui/tests/test_a2ui.py::test_citizen_v1_freeze_matches_every_delivered_artifact`

## Criterio de reevaluación

`citizen:v1` no se reabre por evolución funcional. Si A2UI publica una versión
incompatible o aparece un caso que exige otros componentes, se evalúa y publica
`citizen:v2`, conservando v1 para consumidores existentes. Una excepción de
seguridad en v1 requiere documentar la vulnerabilidad, revisar compatibilidad y
rotar explícitamente las huellas congeladas.
