# Dominio: ganadería

## Objetivo

Consultar historial sanitario, registrar una vacuna y validar reglas de movilización.

## Contenido

Ejemplos: `domain.yaml`, `movement_rules.yaml`, fuentes, fixtures de animal sintético y tools `ganaderia.*`.

## Exclusiones

No diagnosticar, sustituir veterinarios ni generar alertas sin una regla/fuente autorizada.

## Convenciones y dependencias

Toda escritura conserva animal, actor, regla, confirmación y folio. Depende de RAG sanitario, historial y MCP.

Las fuentes y el historial deben conservar consistencia, vigencia y trazabilidad.

## Tareas iniciales

Consulta de animal, requisitos, validación, confirmación de vacuna mock y alerta autorizada.

## Terminado

`CAP-GAN-01` registra folio idempotente y la decisión de movilización puede rastrearse hasta una regla vigente.
