import { useEffect, useState } from "react";
import { type CountRow, request, type Session, type Stats } from "../api";
import { CATEGORY, STATUS } from "../labels";

type Props = { session: Session; onError: (error: unknown) => void };

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function Tile({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {note && <p className="mt-1 text-xs text-slate-500">{note}</p>}
    </div>
  );
}

function Bars({
  title,
  rows,
  names = {},
}: {
  title: string;
  rows: CountRow[];
  names?: Record<string, string>;
}) {
  const shown = rows.filter((row) => row.name !== null);
  const largest = Math.max(...shown.map((row) => row.count), 1);
  return (
    <section className="card">
      <h2 className="mb-3 text-sm font-medium text-slate-500">{title}</h2>
      {shown.length === 0 && <p className="text-sm text-slate-500">Hali ma’lumot yo‘q.</p>}
      <ul className="space-y-2 text-sm">
        {shown.map((row) => (
          <li key={row.name}>
            <div className="flex justify-between gap-3">
              <span>{names[row.name ?? ""] ?? row.name}</span>
              <span className="tabular-nums text-slate-600">{row.count}</span>
            </div>
            <div className="mt-1 h-1.5 rounded bg-slate-100">
              <div
                className="h-1.5 rounded bg-indigo-500"
                style={{ width: `${(row.count / largest) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function StatsPage({ session, onError }: Props) {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    request<Stats>("/stats", session.token).then(setStats).catch(onError);
  }, [session.token, onError]);

  if (!stats) return <p className="text-sm text-slate-500">Yuklanmoqda...</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Rahbar statistikasi</h1>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Tile label="Jami ticketlar" value={String(stats.total)} />
        <Tile
          label="Qo‘lda tekshirilgan"
          value={percent(stats.review_share)}
          note={`${stats.review_total} ta ticket`}
        />
        <Tile
          label="Operator tuzatgan"
          value={percent(stats.correction_share)}
          note={`${stats.corrected} / ${stats.ai_classified} ta AI tasnifi`}
        />
        <Tile
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
        <Bars title="Jamoa bo‘yicha" rows={stats.by_team} />
        <Bars title="Kategoriya bo‘yicha" rows={stats.by_category} names={CATEGORY} />
        <Bars title="Ustuvorlik bo‘yicha" rows={stats.by_priority} />
        <Bars title="Holat bo‘yicha" rows={stats.by_status} names={STATUS} />
      </div>
    </div>
  );
}
