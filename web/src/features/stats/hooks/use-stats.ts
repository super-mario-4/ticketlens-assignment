import { useCallback, useState } from "react";
import { useRequest } from "@/shared/hooks/use-request";
import { fetchStats } from "../api/stats";
import type { StatsPeriod } from "../types";

export function useStats() {
  const [period, setPeriod] = useState<StatsPeriod>({ from: "", to: "" });
  const load = useCallback(() => fetchStats(period), [period]);
  const { data: stats, error, loading } = useRequest(load);
  return { stats, error, loading, period, setPeriod };
}
