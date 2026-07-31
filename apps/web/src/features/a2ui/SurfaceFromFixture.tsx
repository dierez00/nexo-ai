"use client";

/**
 * Carga una superficie A2UI desde un fixture y la renderiza.
 *
 * Es el punto donde hoy entra el JSONL y donde mañana entrará el SSE del run:
 * el renderer no sabe de dónde vino el lote, solo que llegó y no validó o sí.
 * Cuando `RunResult` lleve la superficie, se cambia el `fetch` por el stream y
 * nada más de este árbol se entera.
 */

import { useCallback, useEffect, useState } from "react";

import { A2UIFallback } from "./Fallback";
import { A2UISurface } from "./Surface";
import { processJsonl } from "./processor";
import type { ProcessResult } from "./types";

const DECLARED_ACTIONS = [{ actionId: "act_reserve_01", label: "Reservar cita" }];

export function SurfaceFromFixture({
  name,
  traceId,
  onAction,
  actionPending,
}: {
  name: string;
  traceId?: string;
  onAction?: (actionId: string) => void;
  actionPending?: boolean;
}) {
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve()
      .then(() => fetch(`/fixtures/a2ui/${name}.jsonl`, { cache: "no-store" }))
      .then((response) => response.text())
      .then((text) => {
        if (!cancelled) setResult(processJsonl(text, DECLARED_ACTIONS));
      })
      .catch(() => {
        if (!cancelled) {
          setResult({
            ok: false,
            code: "VALIDATION_FAILED",
            errors: [{ rule: "transport_failed", detail: "no se pudo obtener la superficie" }],
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [name, attempt]);

  if (result === null) {
    return (
      <div
        aria-label="Cargando superficie"
        className="h-32 animate-pulse rounded-xl border border-border bg-muted/40 motion-reduce:animate-none"
      />
    );
  }

  if (!result.ok) {
    // El detalle de las reglas va a consola, no a la pantalla: el fallback no
    // revela por qué falló.
    console.error(
      "[A2UI] VALIDATION_FAILED",
      result.errors.map((error) => error.rule),
    );
    return <A2UIFallback traceId={traceId} onRetry={retry} />;
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
