# Documentación

## Objetivo

Conservar decisiones duraderas, arquitectura, runbooks, guías y coordinación del equipo.

## Debe contener

ADR, diagramas, planes individuales, onboarding, seguridad y guion de demo.

## No debe contener

Secretos, instrucciones obsoletas sin marcar ni duplicación sin owner.

## Convenciones

Enlaces relativos; fecha/estado/decisor en ADR; actualizar documentación al cambiar contratos. Nombres descriptivos en `snake_case` salvo ADR numerados.

Responsabilidad compartida; Dani coordina documentación de release.

## Ejemplos y tareas

`architecture/overview.md`, `adr/0001-modular-monolith.md`, `team/*.md`. Crear ADR principales, onboarding y runbooks.

Runbooks disponibles: [arranque del backend](runbooks/arranque.md) y
[Twilio WhatsApp Sandbox](runbooks/twilio_whatsapp.md).

Dependencias permitidas: puede enlazar cualquier módulo, pero no debe convertirse en una dependencia de ejecución.

## Terminado

Cada decisión no obvia tiene contexto, consecuencias, estado y responsable.
