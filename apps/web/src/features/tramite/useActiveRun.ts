"use client";

/**
 * Resuelve "mi trámite actual" para las páginas de trámite/seguimiento: o el
 * `run_id` que llega por query string (deep link desde el chat/folio), o el
 * run más reciente del ciudadano vía `GET /runs`. No hay endpoint de
 * "expediente"; el snapshot de `RunResult` (con su `surface` y `estimate`) más
 * la lista de eventos ya cubren costos, checklist y línea de tiempo.
 */

import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch, listRuns, type RunEvent, type RunResult } from "@/lib/api/client";

export type ActiveRunState =
  | { status: "loading" }
  | { status: "empty" }
  | { status: "error"; message: string }
  | { status: "loaded"; run: RunResult; events: RunEvent[] };

export function useActiveRun(runIdParam?: string | null) {
  const [state, setState] = useState<ActiveRunState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  const load = useCallback(async (cancelledRef: { current: boolean }) => {
    setState({ status: "loading" });
    try {
      const runId = runIdParam ?? (await listRuns({ limit: 1 }))[0]?.run_id;
      if (cancelledRef.current) return;
      if (!runId) {
        setState({ status: "empty" });
        return;
      }
      const [run, events] = await Promise.all([
        apiFetch<RunResult>(`/api/v1/runs/${runId}`),
        apiFetch<RunEvent[]>(`/api/v1/runs/${runId}/events/list`),
      ]);
      if (!cancelledRef.current) setState({ status: "loaded", run, events });
    } catch (err) {
      if (cancelledRef.current) return;
      setState({
        status: "error",
        message:
          err instanceof ApiError
            ? err.problem.detail || err.problem.title || "La API rechazó la solicitud."
            : "No pudimos conectar con la API. Revisa que el backend esté corriendo.",
      });
    }
  }, [runIdParam]);

  useEffect(() => {
    const cancelledRef = { current: false };
    void Promise.resolve().then(() => load(cancelledRef));
    return () => {
      cancelledRef.current = true;
    };
  }, [load, attempt]);

  return { state, retry: () => setAttempt((value) => value + 1) };
}
