import { Card, CardContent } from "@/shared/components/ui/card";

type Props = { label: string; value: string; note?: string };

export function StatTile({ label, value, note }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
        {note && <p className="mt-1 text-xs text-muted-foreground">{note}</p>}
      </CardContent>
    </Card>
  );
}
