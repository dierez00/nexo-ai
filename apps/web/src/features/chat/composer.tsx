import Link from "next/link";
import { FormEvent, useState } from "react";
import { ArrowUp, Mic } from "lucide-react";

export function ChatComposer({
  disabled = false,
  onSubmit,
}: {
  disabled?: boolean;
  onSubmit?: (content: string) => void;
}) {
  const [value, setValue] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = value.trim();
    if (!content || disabled) return;
    onSubmit?.(content);
    setValue("");
  }

  return (
    <form
      onSubmit={submit}
      className="border-t border-border p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]"
    >
      <div className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-end gap-2 rounded-2xl border border-border bg-background p-2">
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
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
          type="submit"
          aria-label="Enviar consulta"
          disabled={disabled || value.trim().length === 0}
          className="grid size-9 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <ArrowUp className="size-4" />
        </button>
      </div>
      <p className="mt-2 px-1 text-xs text-muted-foreground">
        El asistente pide tu confirmación antes de reservar, pagar o enviar documentos.
      </p>
    </form>
  );
}
