"use client";

/**
 * Renderiza la superficie A2UI que llega en `RunResult.surface`.
 *
 * A diferencia de `SurfaceFromFixture`, no hay red de por medio: el lote ya
 * llegó completo dentro del snapshot del run o de un evento `a2ui.*`, así que
 * solo se traduce el contrato (`fromContract.ts`) y se valida (`processor.ts`).
 * Sin estado propio de carga — si `surface` está presente, ya es momento de
 * intentar dibujarla.
 */

import { useMemo } from "react";

import type { A2UISurface as WireA2UISurface } from "@/generated/contracts";
import { A2UIFallback } from "./Fallback";
import { toA2UIMessages, toDeclaredActions } from "./fromContract";
import { processMessages } from "./processor";
import { A2UISurface } from "./Surface";

export function SurfaceFromRun({
  surface,
  traceId,
  textAlternative,
  onAction,
  actionPending,
}: {
  surface: WireA2UISurface;
  traceId?: string;
  textAlternative?: string;
  onAction?: (actionId: string) => void;
  actionPending?: boolean;
}) {
  const result = useMemo(
    () => processMessages(toA2UIMessages(surface.messages), toDeclaredActions(surface.actions)),
    [surface],
  );

  if (!result.ok) {
    console.error(
      "[A2UI] VALIDATION_FAILED",
      result.errors.map((error) => error.rule),
    );
    return <A2UIFallback traceId={traceId} textAlternative={textAlternative} />;
  }

  return (
    <A2UISurface
      surface={result.surface}
      traceId={traceId}
      onAction={onAction}
      actionPending={actionPending}
    />
  );
}
