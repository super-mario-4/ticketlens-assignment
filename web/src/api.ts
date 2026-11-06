export type Session = { token: string; username: string; role: "operator" | "lead" };

export type TicketItem = {
  id: string;
  source_ticket_id: string;
  channel: string;
  created_at: string;
  status: string;
  review_reason: string | null;
  category: string | null;
  priority: string | null;
  team: string | null;
  summary: string | null;
  confidence: number | null;
  preview: string | null;
};

export type TicketPage = { items: TicketItem[]; total: number; limit: number; offset: number };

export type Classification = {
  model: string;
  prompt_version: string;
  category: string;
  priority: string;
  confidence: number;
  summary: string;
  team: string | null;
  latency_ms: number;
  created_at: string;
};

export type Correction = {
  old_category: string | null;
  new_category: string;
  old_priority: string | null;
  new_priority: string;
  old_team: string | null;
  new_team: string | null;
  reason: string | null;
  corrected_by: string;
  corrected_at: string;
};

export type TicketDetail = TicketItem & {
  text_masked: string | null;
  ingested_at: string;
  classified_at: string | null;
  classifications: Classification[];
  corrections: Correction[];
};

export type Meta = {
  categories: string[];
  priorities: string[];
  channels: string[];
  statuses: string[];
  teams: string[];
  routing: Record<string, string>;
};

export type CountRow = { name: string | null; count: number };

export type Stats = {
  total: number;
  by_status: CountRow[];
  by_team: CountRow[];
  by_category: CountRow[];
  by_priority: CountRow[];
  review_total: number;
  review_share: number;
  ai_classified: number;
  corrected: number;
  correction_share: number;
  routing_count: number;
  routing_seconds_avg: number | null;
};

export type ImportJob = {
  id: string;
  filename: string;
  status: string;
  total: number;
  inserted: number;
  skipped: number;
  errors: { row?: number; id?: string; code: string }[];
};

const SESSION_KEY = "ticketlens-session";

export function loadSession(): Session | null {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    return stored ? (JSON.parse(stored) as Session) : null;
  } catch {
    return null;
  }
}

export function saveSession(session: Session | null): void {
  try {
    if (session) localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    // The session then lasts until the page is closed.
  }
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

export async function request<T>(path: string, token: string | null, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`/api${path}`, { ...init, headers });
  if (response.ok) return (await response.json()) as T;

  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  throw new ApiError(response.status, typeof detail?.code === "string" ? detail.code : "error");
}
