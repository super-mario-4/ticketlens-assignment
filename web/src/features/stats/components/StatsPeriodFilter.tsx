import { X } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import type { StatsPeriod } from "../types";

type Props = { period: StatsPeriod; onChange: (period: StatsPeriod) => void };

export function StatsPeriodFilter({ period, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="space-y-2">
        <Label htmlFor="stats-from">Boshlanish sanasi</Label>
        <Input
          id="stats-from"
          type="date"
          className="w-40 bg-card"
          max={period.to || undefined}
          value={period.from}
          onChange={(event) => onChange({ ...period, from: event.target.value })}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="stats-to">Tugash sanasi</Label>
        <Input
          id="stats-to"
          type="date"
          className="w-40 bg-card"
          min={period.from || undefined}
          value={period.to}
          onChange={(event) => onChange({ ...period, to: event.target.value })}
        />
      </div>
      {(period.from || period.to) && (
        <Button variant="ghost" onClick={() => onChange({ from: "", to: "" })}>
          <X aria-hidden />
          Tozalash
        </Button>
      )}
    </div>
  );
}
