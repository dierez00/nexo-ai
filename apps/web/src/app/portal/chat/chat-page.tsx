"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, ListRestart, SearchX } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { AssistantMessage, TypingIndicator, UserBubble } from "@/features/chat/bubble";
import { ChatTimeline } from "@/features/chat/timeline";
import { AlertCard } from "@/features/chat/actions";
import { ReceiptCard } from "@/features/chat/cards";
import { ChatComposer } from "@/features/chat/composer";
import { PendingActionCard } from "@/features/chat/pending-action-card";
import { SurfaceFromRun } from "@/features/a2ui/SurfaceFromRun";
import { persistFolio } from "@/features/tramite/folio-history";
import type { A2UIAction, Estimate } from "@/generated/contracts";
import {
  ApiError,
  apiFetch,
  clearIdempotencyKey,
  confirmAction,
  eventSourceUrl,
  getOrCreateIdempotencyKey,
  type Conversation,
  type RunAccepted,
  type RunEvent,
  type RunResult,
} from "@/lib/api/client";

type ChatMessage =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; content: string; run?: RunResult | null };

type ChatStatus =
  | "idle"
  | "creating"
  | "streaming"
  | "reconnecting"
  | "waiting_confirmation"
  | "error";

const RUN_EVENT_TYPES = [
  "run.queued",
  "run.planning",
  "run.started",
  "run.waiting_confirmation",
  "run.resumed",
  "run.partial",
  "run.completed",
  "run.failed",
  "run.cancelled",
  "classification.started",
  "classification.completed",
  "classification.failed",
  "plan.created",
  "plan.updated",
  "agent.started",
  "agent.completed",
  "agent.retried",
  "agent.failed",
  "rag.started",
  "rag.completed",
  "rag.filtered",
  "rag.failed",
  "tool.requested",
  "tool.authorized",
  "tool.denied",
  "tool.started",
  "tool.completed",
  "tool.replayed",
  "tool.failed",
  "model.selected",
  "model.fallback",
  "model.completed",
  "model.failed",
  "verification.completed",
  "contradiction.detected",
  "contradiction.resolved",
  "contradiction.unresolved",
  "checkpoint.saved",
  "checkpoint.restored",
  "a2ui.generated",
  "a2ui.validated",
  "a2ui.validation_failed",
  "a2ui.fallback",
  "evaluation.started",
  "evaluation.completed",
  "evaluation.failed",
  "prompt.drafted",
  "prompt.validated",
  "prompt.approved",
  "prompt.rejected",
  "prompt.published",
  "corpus.drafted",
  "corpus.validated",
  "corpus.activated",
  "corpus.rolled_back",
] as const;

const TERMINAL_STATUSES = new Set(["succeeded", "partial", "failed", "cancelled"]);

const ACTIVE_RUN_KEY = "nexo.chat.active_run";

type PersistedRun = { conversation: Conversation; run_id: string; events_url: string };

function readActiveRun(): PersistedRun | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(ACTIVE_RUN_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as PersistedRun;
  } catch {
    window.localStorage.removeItem(ACTIVE_RUN_KEY);
    return null;
  }
}

function persistActiveRun(value: PersistedRun) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACTIVE_RUN_KEY, JSON.stringify(value));
}

function clearActiveRun() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACTIVE_RUN_KEY);
}

function statusLabel(status: ChatStatus) {
  if (status === "creating") return "Preparando conversación";
  if (status === "streaming") return "Ejecutando trámite";
  if (status === "reconnecting") return "Reconectando…";
  if (status === "waiting_confirmation") return "Esperando tu confirmación";
  if (status === "error") return "Sin conexión con la API";
  return "Asistente en línea";
}

function eventDetail(event: RunEvent) {
  const type = event.type.replaceAll(".", " ");
  if (event.error?.message) return event.error.message;
  if (event.public_data && Object.keys(event.public_data).length > 0) {
    return JSON.stringify(event.public_data);
  }
  return type.charAt(0).toUpperCase() + type.slice(1);
}

export function ChatPage() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<{
    runId: string;
    action: A2UIAction;
    estimate: Estimate | null | undefined;
  } | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [receipt, setReceipt] = useState<{ folio: string; label: string } | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const currentRunRef = useRef<{ run_id: string; events_url: string } | null>(null);
  const lastSequenceRef = useRef(0);

  const reset = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    currentRunRef.current = null;
    lastSequenceRef.current = 0;
    clearActiveRun();
    setConversation(null);
    setMessages([]);
    setEvents([]);
    setError(null);
    setPendingAction(null);
    setReceipt(null);
    setStatus("idle");
  }, []);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  function applyRunResult(runId: string, result: RunResult) {
    const answer =
      result.answer ||
      result.error?.message ||
      "El run terminó sin una respuesta textual. Revisa la línea de tiempo para más detalle.";
    setMessages((current) => [
      ...current,
      { id: `assistant-${runId}-${Date.now()}`, role: "assistant", content: answer, run: result },
    ]);

    if (result.status === "waiting_confirmation" && result.available_actions?.length) {
      setPendingAction({ runId, action: result.available_actions[0], estimate: result.estimate });
      setStatus("waiting_confirmation");
    } else {
      setPendingAction(null);
      setStatus("idle");
    }

    if (TERMINAL_STATUSES.has(result.status)) {
      clearActiveRun();
    }
  }

  async function loadRunResult(runId: string) {
    const result = await apiFetch<RunResult>(`/api/v1/runs/${runId}`);
    applyRunResult(runId, result);
  }

  function listenToRun(run: { run_id: string; events_url: string }, lastEventId?: number) {
    eventSourceRef.current?.close();
    currentRunRef.current = { run_id: run.run_id, events_url: run.events_url };
    const source = new EventSource(eventSourceUrl(run.events_url, { lastEventId }));
    eventSourceRef.current = source;
    setStatus("streaming");

    const handleRunEvent = (message: MessageEvent) => {
      if (!message.data) return;
      try {
        const event = JSON.parse(message.data) as RunEvent;
        lastSequenceRef.current = Math.max(lastSequenceRef.current, event.sequence);
        setEvents((current) =>
          current.some((item) => item.sequence === event.sequence) ? current : [...current, event],
        );
      } catch {
        // Los comentarios keepalive no contienen JSON.
      }
    };

    for (const eventType of RUN_EVENT_TYPES) {
      source.addEventListener(eventType, handleRunEvent);
    }

    source.addEventListener("run.status", (message) => {
      // El servidor ya no va a mandar más datos en esta pasada (terminal o
      // `waiting_confirmation`): a diferencia de `onerror`, aquí sí cerramos
      // nosotros. Reabrir tras confirmar es responsabilidad de quien confirma.
      source.close();
      eventSourceRef.current = null;
      try {
        const payload = JSON.parse((message as MessageEvent).data) as { run_id: string };
        void loadRunResult(payload.run_id);
      } catch {
        void loadRunResult(run.run_id);
      }
    });

    source.onopen = () => setStatus("streaming");
    source.onerror = () => {
      // No cerramos la conexión: es la señal de que `EventSource` reintentará
      // solo, mandando `Last-Event-ID` de forma nativa. Cerrar aquí perdería
      // justo ese reintento (`DIE`-style: el backend ya soporta resumir por
      // secuencia, botarlo del lado del cliente sería tirar esa garantía).
      setStatus((current) => (current === "waiting_confirmation" ? current : "reconnecting"));
    };
  }

  // Recuperar el run activo si la página se recargó a mitad de una ejecución.
  useEffect(() => {
    const persisted = readActiveRun();
    if (!persisted) return;
    let cancelled = false;

    (async () => {
      try {
        const [snapshot, timeline] = await Promise.all([
          apiFetch<RunResult>(`/api/v1/runs/${persisted.run_id}`),
          apiFetch<RunEvent[]>(`/api/v1/runs/${persisted.run_id}/events/list`),
        ]);
        if (cancelled) return;
        setConversation(persisted.conversation);
        setEvents(timeline);
        lastSequenceRef.current = timeline.at(-1)?.sequence ?? 0;
        currentRunRef.current = { run_id: persisted.run_id, events_url: persisted.events_url };
        applyRunResult(persisted.run_id, snapshot);
        if (!TERMINAL_STATUSES.has(snapshot.status) && snapshot.status !== "waiting_confirmation") {
          listenToRun(persisted, lastSequenceRef.current);
        }
      } catch {
        if (!cancelled) clearActiveRun();
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function ensureConversation() {
    if (conversation) return conversation;
    const created = await apiFetch<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ channel: "web", title: "Portal ciudadano" }),
    });
    setConversation(created);
    return created;
  }

  async function send(content: string) {
    setError(null);
    setReceipt(null);
    setStatus("creating");
    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content }]);
    try {
      const currentConversation = await ensureConversation();
      const accepted = await apiFetch<RunAccepted>(
        `/api/v1/conversations/${currentConversation.conversation_id}/messages`,
        { method: "POST", body: JSON.stringify({ content }) },
      );
      lastSequenceRef.current = 0;
      setEvents([]);
      persistActiveRun({
        conversation: currentConversation,
        run_id: accepted.run_id,
        events_url: accepted.events_url,
      });
      listenToRun(accepted);
    } catch (err) {
      setStatus("error");
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title || "La API rechazó la solicitud.");
      } else {
        setError("No pudimos conectar con la API. Revisa que el backend esté corriendo.");
      }
    }
  }

  async function respondToAction(consent: boolean) {
    if (!pendingAction) return;
    const { action } = pendingAction;
    setConfirming(true);
    setError(null);
    const idempotencyKey = getOrCreateIdempotencyKey(action.action_id);
    try {
      const result = await confirmAction(
        action.action_id,
        { consent, expected_version: action.expected_version },
        idempotencyKey,
      );
      clearIdempotencyKey(action.action_id);
      setPendingAction(null);

      if (result.status === "succeeded" && result.tool_result?.confirmation) {
        const folio = result.tool_result.confirmation.identifier;
        setReceipt({ folio, label: action.label });
        persistFolio({
          run_id: pendingAction.runId,
          folio,
          label: action.label,
          completed_at: new Date().toISOString(),
        });
      }
      if (result.status === "failed" && result.error) {
        setError(result.error.message);
      }

      const runMeta = currentRunRef.current;
      if (runMeta) listenToRun(runMeta, lastSequenceRef.current);
      else setStatus("idle");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title || "No pudimos confirmar la acción.");
      } else {
        setError("No pudimos conectar con la API para confirmar la acción.");
      }
      setStatus("waiting_confirmation");
    } finally {
      setConfirming(false);
    }
  }

  async function handleSurfaceAction(actionId: string) {
    if (pendingAction && pendingAction.action.action_id === actionId) {
      await respondToAction(true);
    }
  }

  const busy = status === "creating" || status === "streaming";
  const enLinea = status !== "error";

  return (
    <PortalShell bleed>
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-border px-4 py-3 sm:px-6">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">Asistente de trámites</p>
            <StatusBadge
              tone={enLinea ? (status === "reconnecting" ? "warning" : "success") : "destructive"}
              pulse={busy || status === "reconnecting"}
              className="mt-1"
            >
              {statusLabel(status)}
            </StatusBadge>
          </div>
          <button
            onClick={reset}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <ListRestart className="size-3.5" /> Nueva
          </button>
        </div>

        <div
          role="log"
          aria-live="polite"
          className="min-h-0 flex-1 space-y-5 overflow-y-auto px-4 py-5 sm:px-6"
        >
          {messages.length === 0 && !busy ? (
            <div className="flex min-h-[60vh] flex-col items-center justify-center px-2 text-center">
              <span className="wordmark">Nexo AI</span>
              <p className="mt-4 max-w-sm text-2xl font-bold tracking-tight">
                ¿En qué trámite te ayudamos hoy?
              </p>
              <p className="mt-2 max-w-sm text-sm text-muted-foreground">
                Escribe tu consulta. El backend creará una conversación real y transmitirá el run
                por SSE.
              </p>
              <button
                onClick={() => void send("Quiero renovar mi licencia de conducir, ¿qué necesito?")}
                className="mt-6 rounded-xl border border-border bg-card px-4 py-2.5 text-sm transition-colors hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Renovar licencia de conducir
              </button>
            </div>
          ) : null}

          {messages.length === 0 && busy ? (
            <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
              <FileText className="size-6 text-muted-foreground" />
              <p className="mt-3 text-lg font-semibold">Creando conversación</p>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                Estamos preparando el expediente del chat.
              </p>
            </div>
          ) : null}

          {messages.map((message) =>
            message.role === "user" ? (
              <UserBubble key={message.id}>{message.content}</UserBubble>
            ) : (
              <AssistantMessage key={message.id}>
                <p>{message.content}</p>
                {message.run?.surface ? (
                  <div className="mt-3">
                    <SurfaceFromRun
                      surface={message.run.surface}
                      traceId={message.run.trace_id}
                      onAction={(actionId) => void handleSurfaceAction(actionId)}
                      actionPending={confirming}
                    />
                  </div>
                ) : null}
                {message.run?.trace_id ? (
                  <p className="mono text-xs text-muted-foreground">Trace: {message.run.trace_id}</p>
                ) : null}
              </AssistantMessage>
            ),
          )}

          {pendingAction ? (
            <AssistantMessage>
              <PendingActionCard
                action={pendingAction.action}
                estimate={pendingAction.estimate}
                pending={confirming}
                onConfirm={() => void respondToAction(true)}
                onCancel={() => void respondToAction(false)}
              />
            </AssistantMessage>
          ) : null}

          {receipt ? (
            <AssistantMessage>
              <ReceiptCard
                folio={receipt.folio}
                tramite={receipt.label}
                fecha={new Date().toLocaleString("es-BO")}
              />
            </AssistantMessage>
          ) : null}

          {busy ? (
            <div className="space-y-4">
              <TypingIndicator />
              {events.length ? (
                <ChatTimeline
                  eventos={events.slice(-5).map((event, index, list) => ({
                    estado: event.type,
                    detalle: eventDetail(event),
                    tone: event.status === "failed" ? "destructive" : "info",
                    done: index < list.length - 1,
                    active: index === list.length - 1,
                  }))}
                />
              ) : null}
            </div>
          ) : null}

          {error ? (
            <AssistantMessage>
              <AlertCard
                titulo="No pudimos completar la consulta"
                detalle={error}
                traceId={events.at(-1)?.trace_id}
                retryLabel="Intentar de nuevo"
                onRetry={() => setError(null)}
              />
            </AssistantMessage>
          ) : null}

          {!busy && messages.length > 0 && events.length === 0 && !error ? (
            <AssistantMessage>
              <div className="rounded-xl border border-border bg-card p-4 text-center">
                <SearchX className="mx-auto size-5 text-muted-foreground" />
                <p className="mt-2 text-sm font-semibold">Aún no hay eventos del run</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Si el backend terminó muy rápido, la respuesta aparecerá aquí al consultar el
                  snapshot final.
                </p>
              </div>
            </AssistantMessage>
          ) : null}
        </div>

        <ChatComposer disabled={busy || status === "waiting_confirmation"} onSubmit={(content) => void send(content)} />
      </div>
    </PortalShell>
  );
}
