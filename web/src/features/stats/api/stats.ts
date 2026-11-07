import { request } from "@/shared/api/client";
import type { Stats, StatsPeriod } from "../types";

function startOfDay(day: string, addDays = 0): string {
  const date = new Date(`${day}T00:00:00`);
  date.setDate(date.getDate() + addDays);
  return date.toISOString();
}

export function fetchStats({ from, to }: StatsPeriod): Promise<Stats> {
  const params = new URLSearchParams();
  if (from) params.set("start", startOfDay(from));
  // `end` is exclusive and the chosen last day counts in full.
  if (to) params.set("end", startOfDay(to, 1));
  return request<Stats>(`/stats?${params}`);
}
