export type TicketStatus = "pending" | "processing" | "classified" | "needs_review";

export type ReviewReason =
  | "no_content"
  | "unclear"
  | "low_confidence"
  | "injection_suspected"
  | "schema_error"
  | "llm_unavailable"
  | "masking_error";

export type TicketItem = {
  id: string;
  source_ticket_id: string;
  channel: string;
  created_at: string;
  status: TicketStatus;
  review_reason: ReviewReason | null;
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

export type CorrectionRequest = {
  category: string;
  priority: string;
  /** Without a team, the backend takes it from the routing file. */
  team: string | null;
  reason: string | null;
};

export type Meta = {
  categories: string[];
  priorities: string[];
  channels: string[];
  statuses: TicketStatus[];
  teams: string[];
  routing: Record<string, string>;
};

export type TicketFilterValues = {
  category: string;
  priority: string;
  team: string;
  channel: string;
  status: string;
};

export type TicketQuery = TicketFilterValues & { q: string; limit: number; offset: number };
