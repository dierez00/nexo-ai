import { cn } from "@/lib/utils";

/** Riel de trazabilidad: estado → fuente → siguiente acción. */
export function Rail({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <ol className={cn("relative space-y-5", className)}>
      <span
        aria-hidden
        className="absolute bottom-1 left-[0.4375rem] top-1 w-0.5 rounded-full bg-linear-to-b from-accent to-accent/15"
      />
      {children}
    </ol>
  );
}

export function RailItem({
  children,
  active = false,
  done = false,
  className,
}: {
  children: React.ReactNode;
  active?: boolean;
  done?: boolean;
  className?: string;
}) {
  return (
    <li className={cn("relative pl-7", className)}>
      <span
        aria-hidden
        className={cn(
          "rail-node",
          done && "bg-accent",
          active && "ring-4 ring-accent/20",
          !done && !active && "border-border",
        )}
      />
      {children}
    </li>
  );
}
