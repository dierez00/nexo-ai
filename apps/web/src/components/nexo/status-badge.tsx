import { cn } from "@/lib/utils";

export type Tone =
  "neutral" | "success" | "warning" | "destructive" | "info" | "accent" | "primary";

const dotClass: Record<Tone, string> = {
  neutral: "bg-muted-foreground",
  success: "bg-success",
  warning: "bg-warning",
  destructive: "bg-destructive",
  info: "bg-info",
  accent: "bg-accent",
  primary: "bg-primary",
};

const ringClass: Record<Tone, string> = {
  neutral: "border-border bg-muted text-muted-foreground",
  success: "border-success/30 bg-success/10 text-success",
  warning: "border-warning/35 bg-warning/12 text-warning",
  destructive: "border-destructive/30 bg-destructive/10 text-destructive",
  info: "border-info/30 bg-info/10 text-info",
  accent: "border-accent/30 bg-accent/10 text-accent",
  primary: "border-primary/25 bg-primary/10 text-primary",
};

export function StatusBadge({
  tone = "neutral",
  children,
  pulse = false,
  className,
}: {
  tone?: Tone;
  children: React.ReactNode;
  pulse?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium",
        ringClass[tone],
        className,
      )}
    >
      <span
        aria-hidden
        className={cn("size-1.5 shrink-0 rounded-full", dotClass[tone], pulse && "animate-pulse")}
      />
      {children}
    </span>
  );
}
