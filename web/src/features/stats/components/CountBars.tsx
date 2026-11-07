import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Progress } from "@/shared/components/ui/progress";
import type { CountRow } from "../types";

type Props = { title: string; rows: CountRow[]; names?: Record<string, string> };

export function CountBars({ title, rows, names = {} }: Props) {
  const shown = rows.filter((row) => row.name !== null);
  const largest = Math.max(...shown.map((row) => row.count), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          <h2>{title}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {shown.length === 0 && <p className="text-sm text-muted-foreground">Hali ma’lumot yo‘q.</p>}
        <ul className="space-y-2 text-sm">
          {shown.map((row) => {
            const name = names[row.name ?? ""] ?? row.name;
            return (
              <li key={row.name}>
                <div className="flex justify-between gap-3">
                  <span className="min-w-0 break-words">{name}</span>
                  <span className="tabular-nums text-muted-foreground">{row.count}</span>
                </div>
                <Progress
                  aria-label={`${name}: ${row.count}`}
                  className="mt-1 h-1.5"
                  value={(row.count / largest) * 100}
                />
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
