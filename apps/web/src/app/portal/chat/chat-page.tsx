"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, ListRestart, SearchX } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { AssistantMessage, TypingIndicator, UserBubble } from "@/features/chat/bubble";
import { ChatTimeline } from "@/features/chat/timeline";
import { AlertCard } from "@/features/chat/actions";
import { ChatComposer } from "@/features/chat/composer";
import {
  ApiError,
  apiFetch,
  eventSourceUrl,
  type Conversation,
  type RunAccepted,
  type RunEvent,
  type RunResult,
} from "@/lib/api/client";

type ChatMessage =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; content: string; run?: RunResult | null };

type ChatStatus = "idle" | "creating" | "streaming" | "error";

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

function statusLabel(status: ChatStatus) {
  if (status === "creating") return "Preparando conversación";
  if (status === "streaming") return "Ejecutando trámite";
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
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const reset = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setConversation(null);
    setMessages([]);
    setEvents([]);
    setError(null);
    setStatus("idle");
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

  async function loadRunResult(runId: string) {
    const result = await apiFetch<RunResult>(`/api/v1/runs/${runId}`);
    const answer =
      result.answer ||
      result.error?.message ||
      "El run terminó sin una respuesta textual. Revisa la línea de tiempo para más detalle.";
    setMessages((current) => [
      ...current,
      { id: `assistant-${runId}-${Date.now()}`, role: "assistant", content: answer, run: result },
    ]);
  }

  function listenToRun(run: RunAccepted) {
    eventSourceRef.current?.close();
    const source = new EventSource(eventSourceUrl(run.events_url));
    eventSourceRef.current = source;
    setStatus("streaming");

    const handleRunEvent = (message: MessageEvent) => {
      if (!message.data) return;
      try {
        const event = JSON.parse(message.data) as RunEvent;
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
      source.close();
      eventSourceRef.current = null;
      setStatus("idle");
      try {
        const payload = JSON.parse((message as MessageEvent).data) as { run_id: string };
        void loadRunResult(payload.run_id);
      } catch {
        void loadRunResult(run.run_id);
      }
    });

    source.onerror = () => {
      source.close();
      eventSourceRef.current = null;
      setStatus("error");
      setError("Se perdió el stream de eventos. Tu mensaje ya fue enviado; intenta consultar de nuevo.");
    };
  }

  async function send(content: string) {
    setError(null);
    setStatus("creating");
    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content }]);
    try {
      const currentConversation = await ensureConversation();
      const accepted = await apiFetch<RunAccepted>(
        `/api/v1/conversations/${currentConversation.conversation_id}/messages`,
        { method: "POST", body: JSON.stringify({ content }) },
      );
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

  const busy = status === "creating" || status === "streaming";
  const enLinea = status !== "error";

  return (
    <PortalShell bleed>
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-border px-4 py-3 sm:px-6">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">Asistente de trámites</p>
            <StatusBadge tone={enLinea ? "success" : "destructive"} pulse={busy} className="mt-1">
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
                {message.run?.trace_id ? (
                  <p className="mono text-xs text-muted-foreground">Trace: {message.run.trace_id}</p>
                ) : null}
              </AssistantMessage>
            ),
          )}

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

        <ChatComposer disabled={busy} onSubmit={(content) => void send(content)} />
      </div>
    </PortalShell>
  );
}
