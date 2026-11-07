import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { PageHeader } from "@/shared/components/PageHeader";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { CATEGORY, STATUS } from "@/shared/lib/labels";
import { CountBars } from "../components/CountBars";
import { StatsPeriodFilter } from "../components/StatsPeriodFilter";
import { StatTile } from "../components/StatTile";
import { useStats } from "../hooks/use-stats";

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function StatsPage() {
  const { stats, error, loading, period, setPeriod } = useStats();

  return (
    <div className="space-y-4">
      <PageHeader title="Rahbar statistikasi" />
      <StatsPeriodFilter period={period} onChange={setPeriod} />
      {error && <ErrorAlert message={error} />}

      {!stats && loading && <Skeleton className="h-64 w-full" />}

      {stats && (
        <div className="space-y-4" aria-busy={loading}>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Jami ticketlar" value={String(stats.total)} />
            <StatTile
              label="Qo‘lda tekshirilgan"
              value={percent(stats.review_share)}
              note={`${stats.review_total} ta ticket`}
            />
            <StatTile
              label="Operator tuzatgan"
              value={percent(stats.correction_share)}
              note={`${stats.corrected} / ${stats.ai_classified} ta AI tasnifi`}
            />
            <StatTile
              label="O‘rtacha yo‘naltirish vaqti"
              value={
                stats.routing_seconds_avg === null
                  ? "—"
                  : `${(stats.routing_seconds_avg / 60).toFixed(1)} daq`
              }
              note={`${stats.routing_count} ta ticket; navbat yig‘ilsa oshadi`}
            />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <CountBars title="Jamoa bo‘yicha" rows={stats.by_team} />
            <CountBars title="Kategoriya bo‘yicha" rows={stats.by_category} names={CATEGORY} />
            <CountBars title="Ustuvorlik bo‘yicha" rows={stats.by_priority} />
            <CountBars title="Holat bo‘yicha" rows={stats.by_status} names={STATUS} />
          </div>
        </div>
      )}
    </div>
  );
}
