# Twilio WhatsApp Sandbox

Guía operativa de la integración actual de Twilio. Responsable: Dani.

## Alcance actual

Nexo IA recibe mensajes de **WhatsApp mediante Twilio Sandbox**. Valida la firma
del webhook, evita reprocesar el mismo mensaje y responde con TwiML. La integración
actual no envía mensajes mediante la API REST de Twilio: la respuesta se entrega en
el XML que Twilio recibe del webhook.

No forman parte del MVP actual Twilio Voice, mensajes salientes iniciados por el
servidor, adjuntos multimedia ni la persistencia de estados de entrega.

## Endpoints expuestos

Ambos endpoints son públicos para Twilio y no usan `Authorization` de usuario. La
autenticación es exclusivamente la cabecera `X-Twilio-Signature`.

| Método y ruta | Configuración en Twilio | Entrada esperada | Respuesta actual |
|---|---|---|---|
| `POST /webhooks/twilio/whatsapp` | **When a message comes in** | `application/x-www-form-urlencoded`: `MessageSid`, `From`, `To`, `Body` | `200 application/xml` con TwiML y la respuesta del asistente. Si es un duplicado, TwiML vacío. |
| `POST /webhooks/twilio/status` | **Status callback URL** | `application/x-www-form-urlencoded`, incluido normalmente `MessageSid` y `MessageStatus` | `204 No Content`. Verifica la firma pero aún no guarda ni procesa el estado. |

Una firma ausente o inválida produce `403` con `ProblemDetail` y el código
`PERMISSION_DENIED`. No se debe configurar un `Idempotency-Key`: Twilio identifica
el mensaje entrante por `MessageSid`.

## Flujo de mensaje entrante

1. Twilio realiza `POST` al endpoint de WhatsApp con el formulario y
   `X-Twilio-Signature`.
2. La API reconstruye la URL pública como `PUBLIC_BASE_URL + path` y valida la firma
   con `TWILIO_AUTH_TOKEN`.
3. El número de origen se transforma en `pii_ref:<hash>`; el teléfono en claro no se
   persiste.
4. Se localiza o crea una conversación de canal `whatsapp`. En Sandbox el tenant
   asignado actualmente es el demo (`tenant_id = 1`).
5. Si ya existe un mensaje con el mismo `MessageSid` en esa conversación, se devuelve
   un acuse TwiML vacío y no se crea otro run.
6. Para un mensaje nuevo se crea el mensaje, se ejecuta el run y se devuelve el texto
   de la respuesta dentro de TwiML. Por tanto, el webhook espera a que termine el run;
   no es una ejecución asíncrona para este canal todavía.

## Configuración

En `.env` defina estas variables y reinicie la API tras cualquier cambio:

```dotenv
PUBLIC_BASE_URL=https://<dominio-publico-sin-barra-final>
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=<token-secreto>
TWILIO_WHATSAPP_SENDER=whatsapp:+14155238886
TWILIO_WEBHOOK_BASE_URL=https://<dominio-publico>
```

`TWILIO_AUTH_TOKEN` es secreto y se usa para comprobar las firmas. `PUBLIC_BASE_URL`
es la fuente efectiva para esa comprobación; `TWILIO_WEBHOOK_BASE_URL` queda
reservada para la configuración de proveedor y no sustituye a `PUBLIC_BASE_URL` en
la validación actual. `TWILIO_ACCOUNT_SID` y `TWILIO_WHATSAPP_SENDER` deben estar
configurados para la futura mensajería saliente, aunque el flujo entrante actual no
invoca la API REST de Twilio.

Para desarrollo local, exponga el puerto `8000` mediante un túnel HTTPS público y
anónimo. Use exactamente su URL pública, sin `/` final, en `PUBLIC_BASE_URL` y en
la consola de Twilio:

```text
When a message comes in: https://<dominio>/webhooks/twilio/whatsapp
Status callback URL:    https://<dominio>/webhooks/twilio/status
```

Después, una el teléfono al Sandbox con el comando `join <palabra-del-sandbox>` y
envíe un mensaje de prueba.

## Seguridad y operación

- No desactive la validación de firma ni sustituya el webhook por autenticación JWT.
- La URL firmada debe coincidir de forma exacta con la URL externa que usa Twilio.
  Si cambia el túnel, actualice `PUBLIC_BASE_URL`, reinicie la API y actualice ambos
  callbacks en Twilio. Un desajuste devuelve `403`.
- Mantenga el endpoint accesible por HTTPS; un túnel con pantalla de login o
  anti-phishing impide que Twilio entregue los webhooks.
- Los reintentos de Twilio no generan un segundo run cuando conservan el mismo
  `MessageSid`. No se deduplican mensajes distintos aunque tengan el mismo texto.
- El callback `/status` no reejecuta agentes y, por ahora, tampoco actualiza un
  registro de entrega. Úselo como acuse seguro hasta que se implemente ese storage.

## Verificación

Las pruebas herméticas de firma, deduplicación y callback están en
`backend/tests/test_webhooks.py`. Para ejecutarlas:

```powershell
uv run --package nexo-api pytest backend/tests/test_webhooks.py -q
```

Ante un `403`, verifique primero que `PUBLIC_BASE_URL` coincida exactamente con la
URL HTTPS configurada en Twilio y que la API haya sido reiniciada. Para el resto del
arranque local, Docker y despliegue consulte el [runbook de arranque](arranque.md).
