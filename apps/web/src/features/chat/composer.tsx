import Link from "next/link";
import { ArrowUp, Mic } from "lucide-react";

export function ChatComposer({ disabled = false }: { disabled?: boolean }) {
  return (
    <div className="border-t border-border p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]">
      <div className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-end gap-2 rounded-2xl border border-border bg-background p-2">
        <textarea
          rows={1}
          disabled={disabled}
          placeholder="Escribe tu consulta sobre el trámite…"
          className="min-w-0 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50"
        />
        <Link
          href="/agente-voz"
          aria-label="Hablar con el agente de voz"
          className="grid size-9 shrink-0 place-items-center rounded-full border border-border text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Mic className="size-4" />
        </Link>
        <button
          aria-label="Enviar consulta"
          disabled={disabled}
          className="grid size-9 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <ArrowUp className="size-4" />
        </button>
      </div>
      <p className="mt-2 px-1 text-xs text-muted-foreground">
        El asistente pide tu confirmación antes de reservar, pagar o enviar documentos.
      </p>
    </div>
  );
}
