"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  apiFetch,
  clearStoredSession,
  loginWithPassword,
  readStoredSession,
  type StoredSession,
  type UserProfile,
} from "@/lib/api/client";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  status: AuthStatus;
  profile: UserProfile | null;
  session: StoredSession | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<StoredSession | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refreshProfile = useCallback(async () => {
    const stored = readStoredSession();
    if (!stored) {
      setSession(null);
      setStatus("unauthenticated");
      return;
    }
    try {
      const profile = await apiFetch<UserProfile>("/api/v1/users/me");
      const next = { ...stored, profile };
      setSession(next);
      setStatus("authenticated");
    } catch {
      clearStoredSession();
      setSession(null);
      setStatus("unauthenticated");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      await Promise.resolve();
      if (!cancelled) await refreshProfile();
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [refreshProfile]);

  const login = useCallback(async (email: string, password: string) => {
    const next = await loginWithPassword(email, password);
    setSession(next);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(() => {
    clearStoredSession();
    setSession(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      profile: session?.profile ?? null,
      session,
      login,
      logout,
      refreshProfile,
    }),
    [login, logout, refreshProfile, session, status],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return value;
}

export function AuthGate({
  children,
  requireAdmin = false,
}: {
  children: React.ReactNode;
  requireAdmin?: boolean;
}) {
  const { status, profile } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [pathname, router, status]);

  if (status === "loading") {
    return (
      <div className="grid min-h-screen place-items-center bg-background px-4 text-center">
        <div>
          <span className="wordmark">Nexo AI</span>
          <p className="mt-3 text-sm text-muted-foreground">Verificando sesión…</p>
        </div>
      </div>
    );
  }

  if (status !== "authenticated") return null;

  if (requireAdmin && profile?.role !== "admin") {
    return (
      <div className="grid min-h-screen place-items-center bg-background px-4 text-center">
        <div className="max-w-sm">
          <span className="wordmark">Nexo AI</span>
          <h1 className="mt-4 text-xl font-bold">No tienes acceso al panel interno</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Tu sesión está activa, pero tu rol no permite administrar esta institución.
          </p>
        </div>
      </div>
    );
  }

  return children;
}
