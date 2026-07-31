import { cn } from "@/lib/utils";

export function UserBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground animate-in fade-in slide-in-from-bottom-2 motion-reduce:animate-none">
        {children}
      </div>
    </div>
  );
}

export function AssistantMessage({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "max-w-[92%] space-y-3 text-sm leading-relaxed text-foreground animate-in fade-in slide-in-from-bottom-2 motion-reduce:animate-none",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-border bg-card px-4 py-3">
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s] motion-reduce:animate-none" />
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s] motion-reduce:animate-none" />
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground motion-reduce:animate-none" />
    </div>
  );
}
