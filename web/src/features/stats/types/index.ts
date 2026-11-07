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

/** Calendar days in the viewer's time zone, `YYYY-MM-DD`; empty means no limit. */
export type StatsPeriod = { from: string; to: string };
