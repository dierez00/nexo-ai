# Integraciones

## Objetivo

Aislar proveedores externos detrás de puertos estables y simulables.

## Debe contener

Adapters Twilio, modelos/embeddings, almacenamiento y sistemas institucionales mock/reales.

## No debe contener

Reglas de negocio, autorización o secretos versionados.

## Convenciones

Protocol/ABC por adapter; timeout; errores normalizados; mock equivalente; firma y deduplicación de webhooks; circuit breaker cuando aplique.

## Dependencias y responsables

SDKs externos y `contracts`. Dani es responsable; Diego apoya modelos y MCP.

## Ejemplos y tareas

`twilio/whatsapp.py`, `models/gateway.py`, `institutional/mock.py`. Crear fixtures, WhatsApp Sandbox, health/fallback y Voice Pro.

## Terminado

Cambiar mock por sandbox no modifica casos de uso; los fallos producen errores estables y los logs no exponen credenciales.
