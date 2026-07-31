/**
 * Adapta el `A2UISurface` que llega en `RunResult` (contrato generado,
 * snake_case) a las formas que espera este renderer (`types.ts`, camelCase en
 * `A2UIAction`).
 *
 * `A2UISurface.messages` ya viaja en la forma aplanada + camelCase del
 * protocolo de wire (el serializer de `A2UIComponent` en el backend aplana
 * `properties` y el alias generator de `A2UIModel` produce `createSurface`,
 * `updateDataModel`, etc.) — el tipo generado describe la forma de
 * *validación* interna, no el JSON real, así que aquí solo se normaliza
 * `null` a `undefined` y se blinda contra un `properties` anidado residual
 * en vez de reescribir la estructura.
 */

import type {
  A2UIAction as GeneratedA2UIAction,
  A2UIMessage as GeneratedA2UIMessage,
} from "@/generated/contracts";
import type { A2UIAction, A2UIMessage, WireComponent } from "./types";

function normalizeComponent(raw: Record<string, unknown>): WireComponent {
  const { properties, ...rest } = raw;
  if (properties && typeof properties === "object" && !Array.isArray(properties)) {
    return { ...rest, ...(properties as Record<string, unknown>) } as WireComponent;
  }
  return rest as WireComponent;
}

export function toA2UIMessages(messages: GeneratedA2UIMessage[]): A2UIMessage[] {
  return messages.map((message) => ({
    version: message.version ?? "",
    createSurface: message.createSurface ?? undefined,
    updateDataModel: message.updateDataModel ?? undefined,
    updateComponents: message.updateComponents
      ? {
          surfaceId: message.updateComponents.surfaceId,
          components: (message.updateComponents.components as unknown as Record<string, unknown>[]).map(
            normalizeComponent,
          ),
        }
      : undefined,
  }));
}

export function toDeclaredActions(actions: GeneratedA2UIAction[] | undefined): A2UIAction[] {
  if (!actions) return [];
  return actions.map((action) => ({
    actionId: action.action_id,
    label: action.label,
    requiresConfirmation: action.requires_confirmation,
  }));
}
