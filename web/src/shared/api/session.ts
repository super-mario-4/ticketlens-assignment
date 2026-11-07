import { useSyncExternalStore } from "react";

export type Role = "operator" | "lead";

export type Session = { token: string; username: string; role: Role };

const SESSION_KEY = "ticketlens-session";

function loadSession(): Session | null {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    return stored ? (JSON.parse(stored) as Session) : null;
  } catch {
    return null;
  }
}

let current = loadSession();
const listeners = new Set<() => void>();

export function getSession(): Session | null {
  return current;
}

export function setSession(session: Session | null): void {
  current = session;
  try {
    if (session) localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    // The session then lasts until the page is closed.
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useSession(): Session | null {
  return useSyncExternalStore(subscribe, getSession);
}
