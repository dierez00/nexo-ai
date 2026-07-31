"use client";

import { useState } from "react";
import { ChevronDown, FileText, ListRestart, SearchX } from "lucide-react";
import { PortalShell } from "@/components/nexo/portal-shell";
import { StatusBadge } from "@/components/nexo/status-badge";
import { AssistantMessage, TypingIndicator, UserBubble } from "@/features/chat/bubble";
import {
  AppointmentCard,
  CostCard,
  DocumentsCard,
  InfoCard,
  ReceiptCard,
  SourceCard,
  UploadedDocsCard,
} from "@/features/chat/cards";
import { ChatTimeline, ProgressSteps } from "@/features/chat/timeline";
import { AlertCard, ConfirmCard, InlineDatePicker, QuickActions } from "@/features/chat/actions";
import { ChatComposer } from "@/features/chat/composer";
import { SurfaceFromFixture } from "@/features/a2ui/SurfaceFromFixture";
import {
  costosLicencia,
  documentosSubidos,
  estadosChat,
  eventosSeguimiento,
  folioTramite,
  requisitosLicencia,
  sugerenciasIniciales,
  traceIdError,
  type ChatStateId,
} from "@/features/chat/chat-mock";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ChatPage() {
  const [estado, setEstado] = useState<ChatStateId>("bienvenida");
  const [dia, setDia] = useState("12");
  const [hora, setHora] = useState("10:00");
  const [cargandoDesde, setCargandoDesde] = useState<ChatStateId | null>(null);

  function ir(siguiente: ChatStateId, conCarga = false) {
    if (conCarga) {
      setCargandoDesde(estado);
      setEstado("cargando");
      window.setTimeout(() => setEstado(siguiente), 900);
    } else {
      setEstado(siguiente);
    }
  }

  // `cargandoDesde` solo se lee dentro de la rama estado === "cargando" y se reescribe
  // en cada entrada a ese estado, así que un valor viejo nunca llega a observarse.

  const enLinea = estado !== "error";

  return (
    <PortalShell bleed>
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-border px-4 py-3 sm:px-6">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">Asistente de trámites</p>
            <StatusBadge
              tone={enLinea ? "success" : "destructive"}
              pulse={estado === "cargando"}
              className="mt-1"
            >
              {enLinea ? "Asistente en línea" : "Sin conexión con la fuente"}
            </StatusBadge>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                aria-label="Ver otros estados del chat (demo)"
                className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Estados <ChevronDown className="size-3.5" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="max-h-80 overflow-y-auto">
              {estadosChat.map((e) => (
                <DropdownMenuItem key={e.id} onSelect={() => setEstado(e.id)}>
                  {e.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div
          role="log"
          aria-live="polite"
          className="min-h-0 flex-1 space-y-5 overflow-y-auto px-4 py-5 sm:px-6"
        >
          {estado === "bienvenida" ? (
            <div className="flex min-h-[60vh] flex-col items-center justify-center px-2 text-center">
              <span className="wordmark">Nexo AI</span>
              <p className="mt-4 max-w-sm text-2xl font-bold tracking-tight">
                ¿En qué trámite te ayudamos hoy?
              </p>
              <p className="mt-2 max-w-sm text-sm text-muted-foreground">
                Escribe tu consulta o elige una sugerencia. Nunca reservamos, pagamos ni enviamos
                nada sin tu confirmación.
              </p>
              <ul className="mt-6 grid w-full max-w-md gap-2">
                {sugerenciasIniciales.map((s) => (
                  <li key={s}>
                    <button
                      onClick={() => ir("respuesta", true)}
                      className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-left text-sm transition-colors hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {estado === "vacio" ? (
            <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
              <FileText className="size-6 text-muted-foreground" />
              <p className="mt-3 text-lg font-semibold">Aún no hay mensajes</p>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                Cuéntanos qué necesitas resolver y te acompañamos paso a paso, sin salir de esta
                pantalla.
              </p>
            </div>
          ) : null}

          {estado === "cargando" ? (
            <div className="space-y-4">
              {cargandoDesde && cargandoDesde !== "bienvenida" ? null : (
                <UserBubble>Quiero renovar mi licencia de conducir</UserBubble>
              )}
              <TypingIndicator />
            </div>
          ) : null}

          {estado === "error" ? (
            <div className="space-y-5">
              <UserBubble>¿Cuánto cuesta el arancel de renovación?</UserBubble>
              <AssistantMessage>
                <AlertCard
                  titulo="No pudimos consultar el arancel vigente"
                  detalle="El servicio de tarifas de la institución no respondió. Tu conversación quedó guardada y no se hizo ningún cobro."
                  traceId={traceIdError}
                  retryLabel="Reintentar consulta"
                  onRetry={() => ir("respuesta", true)}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "sin-resultados" ? (
            <div className="space-y-5">
              <UserBubble>¿Cómo registro una marca comercial?</UserBubble>
              <AssistantMessage>
                <div className="rounded-xl border border-border bg-card p-4 text-center">
                  <SearchX className="mx-auto size-5 text-muted-foreground" />
                  <p className="mt-2 text-sm font-semibold">No encontramos ese trámite</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Registro de marcas no está disponible en este portal todavía. Prueba con una de
                    estas opciones.
                  </p>
                </div>
                <QuickActions
                  acciones={[
                    { texto: "Ver trámites disponibles", onClick: () => ir("bienvenida") },
                    { texto: "Hablar con una persona", onClick: () => ir("bienvenida") },
                  ]}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "respuesta" ? (
            <div className="space-y-5">
              <UserBubble>Quiero renovar mi licencia de conducir, ¿qué hago?</UserBubble>
              <AssistantMessage>
                <p>
                  Con gusto. La renovación se hace en la Oficina Central de Tránsito y toma una sola
                  visita si llevas todo listo. Estos son los requisitos:
                </p>
                <DocumentsCard items={requisitosLicencia} />
                <SourceCard
                  titulo="Reglamento de Tránsito — Artículo 22, renovación de licencia"
                  actualizado="12/06/2026"
                  doc="doc_22-lic"
                />
                <QuickActions
                  acciones={[
                    { texto: "Ya tengo mis documentos", onClick: () => ir("requisitos", true) },
                  ]}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "requisitos" ? (
            <div className="space-y-5">
              <UserBubble>Ya tengo mis documentos, ¿cómo sigo?</UserBubble>
              <AssistantMessage>
                <ProgressSteps paso={3} total={5} label="Renovación de licencia" />
                <UploadedDocsCard items={documentosSubidos} />
                <CostCard items={costosLicencia} total="250,00 Bs" />
                <p>
                  Falta subir tu licencia anterior. En cuanto la tengamos, puedes reservar tu cita.
                </p>
                <QuickActions
                  acciones={[{ texto: "Agendar cita", onClick: () => ir("agendar") }]}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "agendar" ? (
            <div className="space-y-5">
              <UserBubble>Agéndame para el 12 de agosto en la mañana</UserBubble>
              <AssistantMessage>
                <InlineDatePicker
                  dia={dia}
                  hora={hora}
                  onDia={setDia}
                  onHora={setHora}
                  onConfirmar={() => ir("cita-confirmada")}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "cita-confirmada" ? (
            <div className="space-y-5">
              <UserBubble>
                Agéndame para el {dia} de agosto a las {hora}
              </UserBubble>
              <AssistantMessage>
                <ConfirmCard
                  titulo={`Vas a reservar una cita el ${dia}/08 a las ${hora} en la Oficina Central de Tránsito.`}
                  detalles={[
                    "Trámite: renovación de licencia · Andrea Peñaranda",
                    "Duración estimada: 30 minutos",
                    "Costo del arancel: 250,00 Bs",
                  ]}
                  onConfirmar={() => ir("tramite-completado", true)}
                  onCancelar={() => ir("agendar")}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "tramite-completado" ? (
            <div className="space-y-5">
              <UserBubble>Confirmar reserva</UserBubble>
              <AssistantMessage>
                <AppointmentCard
                  fecha={`${dia} de agosto · ${hora}`}
                  tramite="Renovación de licencia · Andrea Peñaranda"
                  lugar="Oficina Central de Tránsito, Av. Libertad 1204, ventanilla 6"
                  duracion="Duración estimada: 30 minutos. Llega 10 minutos antes."
                />
                <ReceiptCard
                  folio={folioTramite}
                  tramite="Renovación de licencia"
                  fecha="30 jul 2026 · 09:41"
                />
                <QuickActions
                  acciones={[
                    { texto: "Ver seguimiento del trámite", onClick: () => ir("seguimiento") },
                  ]}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "seguimiento" ? (
            <div className="space-y-5">
              <UserBubble>¿Cómo va mi trámite?</UserBubble>
              <AssistantMessage>
                <InfoCard eyebrow="Folio del trámite" title={folioTramite} />
                <ChatTimeline eventos={eventosSeguimiento} />
                <QuickActions
                  acciones={[
                    { texto: "Subir documento faltante", onClick: () => ir("requisitos") },
                    { texto: "Empezar de nuevo", onClick: () => ir("bienvenida") },
                  ]}
                />
              </AssistantMessage>
            </div>
          ) : null}

          {estado === "surface-a2ui" ? (
            <div className="space-y-5">
              <UserBubble>Quiero renovar mi licencia de conducir, ¿qué necesito?</UserBubble>
              <AssistantMessage>
                {/* Misma conversación, pero la respuesta la declara el servidor
                    como superficie A2UI en vez de armarla el frontend. */}
                <SurfaceFromFixture name="valid__catalog" traceId="trc_demo_a2ui" />
                <p className="text-xs text-muted-foreground">
                  Superficie declarativa del catálogo <span className="mono">citizen:v1</span>,
                  validada contra la allowlist antes de dibujarse.
                </p>
              </AssistantMessage>
            </div>
          ) : null}
        </div>

        <div className="border-t border-border px-4 py-2 sm:px-6">
          <button
            onClick={() => ir("bienvenida")}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <ListRestart className="size-3.5" /> Empezar una nueva conversación
          </button>
        </div>
        <ChatComposer disabled={estado === "cargando"} />
      </div>
    </PortalShell>
  );
}
