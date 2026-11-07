import { getSession, setSession } from "./session";

export type ErrorDetail = { code?: unknown; [key: string]: unknown };

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly detail: ErrorDetail | null = null,
  ) {
    super(code);
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getSession()?.token;
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`/api${path}`, { ...init, headers });
  if (response.ok) return (await response.json()) as T;

  // An expired token ends the session instead of showing errors on every page.
  // Without a token this is a failed login, which the login form reports itself.
  if (response.status === 401 && token) setSession(null);

  const body = await response.json().catch(() => null);
  const detail: ErrorDetail | null = body?.detail ?? null;
  throw new ApiError(
    response.status,
    typeof detail?.code === "string" ? detail.code : "error",
    detail,
  );
}
