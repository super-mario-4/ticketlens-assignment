import { Badge } from "@/shared/components/ui/badge";

const PRIORITY_STYLE: Record<string, string> = {
  Critical: "border-transparent bg-red-100 text-red-800",
  High: "border-transparent bg-orange-100 text-orange-800",
  Medium: "border-transparent bg-amber-100 text-amber-800",
  Low: "border-transparent bg-slate-100 text-slate-700",
};

export function PriorityBadge({ priority }: { priority: string | null }) {
  if (!priority) return <span className="text-muted-foreground">—</span>;
  return (
    <Badge variant="outline" className={PRIORITY_STYLE[priority]}>
      {priority}
    </Badge>
  );
}
