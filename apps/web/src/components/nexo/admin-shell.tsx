"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ListTree, Workflow, Boxes, Plug, Layers, Menu, X } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/admin/runs", label: "Runs", icon: ListTree, exact: false },
  { to: "/admin/workflow", label: "Workflow", icon: Workflow, exact: false },
  { to: "/admin/catalogo", label: "Catálogo", icon: Boxes, exact: false },
  { to: "/admin/integraciones", label: "Integraciones", icon: Plug, exact: false },
  { to: "/admin/a2ui-lab", label: "Banco A2UI", icon: Layers, exact: false },
] as const;

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <ul className="space-y-1">
      {nav.map((item) => {
        const active = item.exact ? pathname === item.to : pathname.startsWith(item.to);
        return (
          <li key={item.to}>
            <Link
              href={item.to}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground",
                active && "bg-secondary text-secondary-foreground",
              )}
            >
              <item.icon className="size-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function AdminShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col border-r border-border bg-sidebar px-3 py-4 lg:flex">
        <div className="px-3 pb-6">
          <span className="wordmark">Nexo AI · Consola</span>
          <p className="mt-2 text-sm font-semibold">Operaciones</p>
        </div>
        <NavList />
        <div className="mt-auto rounded-xl border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground">Sesión de demostración</p>
          <p className="mt-0.5 truncate text-sm font-medium">m.rivas@nexo.gob</p>
        </div>
      </aside>

      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Cerrar navegación"
            className="absolute inset-0 bg-foreground/40"
            onClick={() => setOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 flex w-64 flex-col border-r border-border bg-sidebar px-3 py-4">
            <div className="mb-6 flex items-center justify-between px-2">
              <span className="wordmark">Nexo AI · Consola</span>
              <button
                onClick={() => setOpen(false)}
                aria-label="Cerrar navegación"
                className="rounded-full p-1 text-muted-foreground"
              >
                <X className="size-4" />
              </button>
            </div>
            <NavList onNavigate={() => setOpen(false)} />
          </div>
        </div>
      ) : null}

      <div className="lg:pl-60">
        <header className="sticky top-0 z-30 border-b border-border/70 bg-background/85 backdrop-blur">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-2">
              <button
                onClick={() => setOpen(true)}
                aria-label="Abrir navegación"
                className="inline-flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-card text-muted-foreground lg:hidden"
              >
                <Menu className="size-4" />
              </button>
              <span className="wordmark truncate">Panel interno</span>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Link
                href="/portal"
                className="hidden rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground sm:inline-flex"
              >
                Ver portal ciudadano
              </Link>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <main className={cn("px-4 py-6 sm:px-6 sm:py-8")}>
          <div className="mb-6 grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4 sm:flex sm:items-center sm:justify-between">
            <div className="min-w-0">
              <h1 className="truncate text-2xl font-bold tracking-tight">{title}</h1>
              {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
            </div>
            {actions ? <div className="shrink-0">{actions}</div> : null}
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
