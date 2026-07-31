"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { ThemeToggle } from "@/components/nexo/theme-toggle";
import { StatusBadge } from "@/components/nexo/status-badge";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/session";

export function LoginForm() {
  const { login, status, profile } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/portal";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") {
      router.replace(next);
    }
  }, [next, router, status]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.replace(next);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title || "No pudimos iniciar sesión.");
      } else {
        setError("No pudimos iniciar sesión. Revisa tu conexión e intenta de nuevo.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto grid max-w-5xl grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-4 sm:px-6">
        <Link href="/" className="wordmark truncate">
          Nexo AI
        </Link>
        <ThemeToggle />
      </header>

      <main className="mx-auto grid max-w-5xl gap-8 px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-[minmax(0,1fr)_380px] lg:items-center">
        <section>
          <StatusBadge tone="accent">Supabase Auth conectado</StatusBadge>
          <h1 className="mt-5 max-w-xl text-3xl font-extrabold leading-tight tracking-tight sm:text-5xl">
            Entra con tu cuenta institucional.
          </h1>
          <p className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
            La sesión se valida con Supabase y el backend resuelve tu institución, rol y permisos
            antes de mostrar el portal o la consola.
          </p>
          {profile ? (
            <p className="mt-5 text-sm text-muted-foreground">Sesión detectada: {profile.email}</p>
          ) : null}
        </section>

        <form onSubmit={onSubmit} className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-full bg-secondary text-secondary-foreground">
              <LockKeyhole className="size-5" />
            </span>
            <div>
              <h2 className="text-lg font-bold">Iniciar sesión</h2>
              <p className="text-sm text-muted-foreground">Usa el email invitado en Supabase.</p>
            </div>
          </div>

          <label className="mt-5 block text-sm font-medium">
            Email
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              autoComplete="email"
              required
              className="mt-2 w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>

          <label className="mt-4 block text-sm font-medium">
            Contraseña
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
              required
              className="mt-2 w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>

          {error ? (
            <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <Button type="submit" disabled={submitting} className="mt-5 w-full rounded-full">
            {submitting ? "Entrando…" : "Entrar"} <ArrowRight className="size-4" />
          </Button>
        </form>
      </main>
    </div>
  );
}
