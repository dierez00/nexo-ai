"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LogOut, MessageSquare, Mic, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { AuthGate, useAuth } from "@/lib/auth/session";
import { ThemeToggle } from "./theme-toggle";

const nav = [
  { to: "/portal", label: "Inicio", icon: Home, adminOnly: false },
  { to: "/portal/chat", label: "Chat", icon: MessageSquare, adminOnly: false },
  { to: "/agente-voz", label: "Voz", icon: Mic, adminOnly: false },
  { to: "/admin/panel", label: "Admin", icon: ShieldCheck, adminOnly: true },
] as const;

export function PortalShell({
  title,
  subtitle,
  bleed = false,
  children,
}: {
  title?: string;
  subtitle?: string;
  bleed?: boolean;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { profile, logout } = useAuth();
  const visibleNav = nav.filter((item) => !item.adminOnly || profile?.role === "admin");

  return (
    <AuthGate>
      <div className={cn("min-h-screen bg-background pb-20 md:pb-0", bleed && "flex flex-col")}>
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto grid max-w-5xl grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 sm:px-6">
          <Link href="/portal" className="min-w-0">
            <span className="wordmark">Nexo AI · Portal ciudadano</span>
          </Link>
          <div className="flex shrink-0 items-center gap-2">
            <nav className="hidden items-center gap-1 md:flex">
              {visibleNav.map((item) => {
                const active =
                  item.to === "/portal" ? pathname === item.to : pathname.startsWith(item.to);
                return (
                  <Link
                    key={item.to}
                    href={item.to}
                    className={cn(
                      "rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground",
                      active && "bg-secondary text-secondary-foreground",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <span className="hidden max-w-36 truncate text-xs text-muted-foreground sm:inline">
              {profile?.name ?? profile?.email}
            </span>
            <ThemeToggle />
            <button
              onClick={logout}
              aria-label="Cerrar sesión"
              className="grid size-8 shrink-0 place-items-center rounded-full border border-border text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <LogOut className="size-3.5" />
            </button>
          </div>
        </div>
      </header>

      {bleed ? (
        <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col overflow-hidden">
          {children}
        </main>
      ) : (
        <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
          {title ? (
            <div className="mb-6">
              <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
              {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
            </div>
          ) : null}
          {children}
        </main>
      )}

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-card/95 backdrop-blur md:hidden">
        <ul className="mx-auto grid max-w-sm" style={{ gridTemplateColumns: `repeat(${visibleNav.length}, minmax(0, 1fr))` }}>
          {visibleNav.map((item) => {
            const active =
              item.to === "/portal" ? pathname === item.to : pathname.startsWith(item.to);
            return (
              <li key={item.to}>
                <Link
                  href={item.to}
                  className={cn(
                    "flex flex-col items-center gap-1 py-3 text-xs font-medium text-muted-foreground",
                    active && "text-accent",
                  )}
                >
                  <item.icon className="size-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      </div>
    </AuthGate>
  );
}
