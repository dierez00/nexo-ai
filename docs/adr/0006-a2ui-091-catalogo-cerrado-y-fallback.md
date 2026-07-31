# 0006 — A2UI v0.9.1, catálogo cerrado y fallback seguro

- **Estado:** accepted
- **Fecha:** 2026-07-30
- **Decisor:** Diego
- **Revisan:** Cris (renderer, accesibilidad y catálogos)
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
- Añadir un componente es una decisión revisable en PR.

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
- Catálogos y fixtures de referencia en `.agents/skills/build-a2ui-frontend/assets/`.

## Criterio de reevaluación

Se reabre si A2UI publica una versión incompatible que aporte lo suficiente para
justificar migrar, o si el catálogo cerrado impide un caso de uso real que no
pueda resolverse añadiendo componentes.
