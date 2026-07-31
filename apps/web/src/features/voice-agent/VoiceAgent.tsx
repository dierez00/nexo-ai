"use client";

import { useCallback, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Conversation } from "@elevenlabs/client";

import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge, type Tone } from "@/components/nexo/status-badge";
import { cn } from "@/lib/utils";

const AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID;

type ConversationStatus = "idle" | "connecting" | "connected" | "error";

type Caption = {
  id: number;
  text: string;
  source: "user" | "ai";
};

const log = (...args: unknown[]) => console.log("[Agente IA]", ...args);
const logError = (...args: unknown[]) => console.error("[Agente IA]", ...args);

// Mensajes más largos usan letra más chica para que nunca se corten.
function captionFontSize(text: string) {
  const length = text.length;
  if (length > 220) return "clamp(1.15rem, 2.4vw, 1.85rem)";
  if (length > 140) return "clamp(1.35rem, 2.8vw, 2.25rem)";
  if (length > 80) return "clamp(1.6rem, 3.4vw, 2.75rem)";
  return "clamp(1.9rem, 4.2vw, 3.5rem)";
}

const STATUS_META: Record<ConversationStatus, { label: string; tone: Tone }> = {
  idle: { label: "Desconectado", tone: "neutral" },
  connecting: { label: "Conectando", tone: "warning" },
  connected: { label: "Conectado", tone: "success" },
  error: { label: "Error de conexión", tone: "destructive" },
};

export default function VoiceAgent() {
  const [status, setStatus] = useState<ConversationStatus>("idle");
  const [caption, setCaption] = useState<Caption | null>(null);
  const [micMuted, setMicMuted] = useState(false);
  const sessionRef = useRef<Awaited<ReturnType<typeof Conversation.startSession>> | null>(null);
  const startTimeRef = useRef(0);
  const idCounterRef = useRef(0);
  // onModeChange puede dispararse antes de que startSession resuelva, cuando
  // sessionRef todavía es null. Guardamos la intención y la aplicamos al conectar.
  const desiredMuteRef = useRef(false);

  const showCaption = useCallback((text: string, source: "user" | "ai") => {
    idCounterRef.current += 1;
    setCaption({ id: idCounterRef.current, text, source });
  }, []);

  const applyMute = useCallback((shouldMute: boolean) => {
    desiredMuteRef.current = shouldMute;
    sessionRef.current?.setMicMuted(shouldMute);
    setMicMuted(shouldMute);
  }, []);

  const handleStart = useCallback(async () => {
    if (!AGENT_ID) {
      logError("Falta NEXT_PUBLIC_ELEVENLABS_AGENT_ID en el entorno (.env.local).");
      setStatus("error");
      return;
    }

    try {
      log("Solicitando permiso de micrófono...");
      setStatus("connecting");
      setCaption(null);
      await navigator.mediaDevices.getUserMedia({ audio: true });
      log("Permiso de micrófono concedido.");

      log("Iniciando sesión...");
      startTimeRef.current = performance.now();
      desiredMuteRef.current = false;
      setMicMuted(false);

      const session = await Conversation.startSession({
        agentId: AGENT_ID,
        // WebRTC (LiveKit) conecta más rápido y con menor latencia que websocket (el default del SDK).
        connectionType: "webrtc",

        onConnect: ({ conversationId }) => {
          const elapsedMs = Math.round(performance.now() - startTimeRef.current);
          log(`Conectado en ${elapsedMs}ms. conversationId:`, conversationId);
          setStatus("connected");
        },

        onDisconnect: () => {
          log("Desconectado del agente.");
          sessionRef.current = null;
          desiredMuteRef.current = false;
          setMicMuted(false);
          setStatus("idle");
        },

        onError: (message, context) => {
          logError("Error en la llamada:", message, context);
          setStatus("error");
        },

        // Silenciamos el micrófono mientras la agente habla para que su propia voz
        // (o un ruido nuestro) no la interrumpa, y lo reactivamos al terminar.
        onModeChange: ({ mode }) => {
          log("Cambio de modo:", mode);
          applyMute(mode === "speaking");
        },

        onStatusChange: ({ status: sdkStatus }) => {
          log("Cambio de estado SDK:", sdkStatus);
        },

        // El SDK entrega { message: string, source: 'user' | 'ai' } — no "text".
        onMessage: ({ message, source }) => {
          log(`Mensaje recibido (source=${source}):`, message);
          showCaption(message, source);
        },
      });

      sessionRef.current = session;
      // Si la agente ya empezó a hablar mientras conectábamos, el mute quedó pendiente.
      if (desiredMuteRef.current) {
        session.setMicMuted(true);
      }
    } catch (error) {
      logError("No se pudo iniciar la sesión:", error);
      setStatus("error");
    }
  }, [applyMute, showCaption]);

  const handleStop = useCallback(async () => {
    if (sessionRef.current) {
      log("Finalizando sesión manualmente...");
      await sessionRef.current.endSession();
      sessionRef.current = null;
      log("Sesión finalizada.");
    }
    desiredMuteRef.current = false;
    setMicMuted(false);
    setStatus("idle");
  }, []);

  const isConnected = status === "connected";
  const isConnecting = status === "connecting";

  const placeholder =
    status === "error"
      ? "No pudimos conectar el audio. Revisa tu micrófono e inténtalo otra vez."
      : isConnecting
        ? "Estableciendo la llamada…"
        : "Presiona iniciar llamada para hablar con el agente";

  return (
    <PortalShell bleed>
      <section className="flex flex-1 items-center justify-center px-6 py-10">
        <AnimatePresence mode="popLayout" initial={false}>
          {caption ? (
            <motion.p
              key={caption.id}
              initial={{ opacity: 0, y: 48 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -56 }}
              transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="m-0 max-w-3xl text-balance text-center font-bold leading-tight tracking-tight text-foreground"
              style={{ fontSize: captionFontSize(caption.text) }}
            >
              {caption.text}
            </motion.p>
          ) : (
            <motion.p
              key="placeholder"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="m-0 max-w-3xl text-center text-2xl font-bold leading-snug tracking-tight text-muted-foreground/60 sm:text-3xl"
            >
              {placeholder}
            </motion.p>
          )}
        </AnimatePresence>
      </section>

      <footer className="flex flex-col items-center gap-4 px-6 pb-10">
        <div className="flex flex-wrap items-center justify-center gap-2">
          <StatusBadge tone={STATUS_META[status].tone} pulse={isConnecting}>
            {STATUS_META[status].label}
          </StatusBadge>

          {isConnected ? (
            <StatusBadge tone={micMuted ? "warning" : "success"} pulse={micMuted}>
              {micMuted ? "Micrófono en silencio" : "Micrófono activo"}
            </StatusBadge>
          ) : null}
        </div>

        <button
          type="button"
          onClick={isConnected ? handleStop : handleStart}
          disabled={isConnecting}
          className={cn(
            "w-full max-w-xs rounded-full px-8 py-4 text-base font-semibold transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60",
            isConnected
              ? "bg-destructive text-destructive-foreground"
              : "bg-primary text-primary-foreground",
          )}
        >
          {isConnected ? "Colgar" : isConnecting ? "Conectando…" : "Iniciar llamada"}
        </button>

        <p className="max-w-sm text-center text-xs text-muted-foreground">
          La llamada se transcribe para mostrarte lo que entendimos. Nada se envía sin tu
          confirmación.
        </p>
      </footer>
    </PortalShell>
  );
}
