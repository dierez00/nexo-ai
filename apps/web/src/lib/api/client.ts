import type { RunEvent, RunResult } from "@/generated/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_NEXO_API_URL ?? "http://localhost:8000";
const SESSION_KEY = "nexo.auth.v1";

export type ProblemDetails = {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  code?: string;
  retryable?: boolean;
  trace_id?: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type UserProfile = {
  user_id: string;
  auth_user_id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  institution?: { tenant_id: string; name: string; slug: string } | null;
  branch?: { branch_id: string; code: string; name: string } | null;
  is_owner?: boolean;
  preferences?: Record<string, unknown>;
};

export type LoginResponse = {
  tokens: TokenPair;
  profile: UserProfile;
};

export type StoredSession = LoginResponse & {
  saved_at: string;
};

export type Conversation = {
  conversation_id: string;
  channel: string;
  status: string;
  title?: string | null;
  created_at: string;
};

export type RunAccepted = {
  run_id: string;
  trace_id: string;
  status: string;
  events_url: string;
  created_at: string;
};

export type MetricSet = {
  window: { start: string; end: string };
  runs: {
    total: number;
    by_status: Record<string, number>;
    by_domain: Record<string, number>;
    avg_latency_ms: number;
    total_cost_usd: number;
  };
  conversations_total: number;
  actions: { total: number; by_status: Record<string, number> };
  appointments: { total: number; by_status: Record<string, number> };
  generated_at: string;
};

export type AdminCatalog = {
  modules: { code: string; name: string; is_core: boolean; enabled: boolean }[];
  roles: { code: string; name: string; is_system: boolean }[];
  permissions: { code: string; module_code?: string | null }[];
};

export type NexoConfigSummary = {
  catalogs?: unknown;
  tools?: unknown;
  policies?: unknown;
  permissions?: unknown;
  model_router?: unknown;
};

export class ApiError extends Error {
  status: number;
  problem: ProblemDetails;

  constructor(status: number, problem: ProblemDetails) {
    super(problem.detail || problem.title || `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

function hasStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function readStoredSession(): StoredSession | null {
  if (!hasStorage()) return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function writeStoredSession(response: LoginResponse): StoredSession {
  const session = { ...response, saved_at: new Date().toISOString() };
  if (hasStorage()) {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }
  return session;
}

export function clearStoredSession() {
  if (hasStorage()) {
    window.localStorage.removeItem(SESSION_KEY);
  }
}

function urlFor(path: string) {
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseError(response: Response): Promise<ProblemDetails> {
  try {
    return (await response.json()) as ProblemDetails;
  } catch {
    return { status: response.status, title: response.statusText || "Error de API" };
  }
}

async function refreshStoredSession(): Promise<StoredSession | null> {
  const current = readStoredSession();
  if (!current?.tokens.refresh_token) return null;

  const response = await fetch(urlFor("/api/v1/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: current.tokens.refresh_token }),
  });
  if (!response.ok) {
    clearStoredSession();
    return null;
  }
  return writeStoredSession((await response.json()) as LoginResponse);
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  options: { auth?: boolean; retryOnUnauthorized?: boolean } = {},
): Promise<T> {
  const { auth = true, retryOnUnauthorized = true } = options;
  const session = auth ? readStoredSession() : null;
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  if (auth && session?.tokens.access_token) {
    headers.set("Authorization", `Bearer ${session.tokens.access_token}`);
  }

  const response = await fetch(urlFor(path), { ...init, headers });
  if (response.status === 401 && auth && retryOnUnauthorized) {
    const refreshed = await refreshStoredSession();
    if (refreshed) {
      const retryHeaders = new Headers(headers);
      retryHeaders.set("Authorization", `Bearer ${refreshed.tokens.access_token}`);
      const retry = await fetch(urlFor(path), { ...init, headers: retryHeaders });
      if (retry.ok) return (await retry.json()) as T;
      throw new ApiError(retry.status, await parseError(retry));
    }
  }
  if (!response.ok) throw new ApiError(response.status, await parseError(response));
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function loginWithPassword(email: string, password: string): Promise<StoredSession> {
  const response = await apiFetch<LoginResponse>(
    "/api/v1/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) },
    { auth: false },
  );
  return writeStoredSession(response);
}

export function eventSourceUrl(eventsUrl: string) {
  const session = readStoredSession();
  const url = new URL(urlFor(eventsUrl));
  if (session?.tokens.access_token) {
    url.searchParams.set("access_token", session.tokens.access_token);
  }
  return url.toString();
}

export type { RunEvent, RunResult };
