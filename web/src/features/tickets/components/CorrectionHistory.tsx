import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { dateText } from "@/shared/lib/format";
import { CATEGORY } from "@/shared/lib/labels";
import type { Correction } from "../types";

export function CorrectionHistory({ corrections }: { corrections: Correction[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          <h2>Tuzatishlar tarixi</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm">
          {corrections.map((item) => (
            <li key={item.corrected_at}>
              {dateText(item.corrected_at)}, {item.corrected_by}:{" "}
              {CATEGORY[item.old_category ?? ""] ?? "—"} →{" "}
              {CATEGORY[item.new_category] ?? item.new_category}, {item.old_priority ?? "—"} →{" "}
              {item.new_priority}, {item.old_team ?? "—"} → {item.new_team ?? "—"}
              {item.reason && <span className="text-muted-foreground"> ({item.reason})</span>}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
