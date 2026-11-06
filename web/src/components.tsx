const PRIORITY_STYLE: Record<string, string> = {
  Critical: "bg-red-100 text-red-800",
  High: "bg-orange-100 text-orange-800",
  Medium: "bg-amber-100 text-amber-800",
  Low: "bg-slate-100 text-slate-700",
};

export function PriorityBadge({ priority }: { priority: string | null }) {
  if (!priority) return <span className="text-slate-400">—</span>;
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLE[priority]}`}>
      {priority}
    </span>
  );
}
