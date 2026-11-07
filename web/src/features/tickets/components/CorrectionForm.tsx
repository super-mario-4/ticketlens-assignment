import { type FormEvent, useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Textarea } from "@/shared/components/ui/textarea";
import { CATEGORY } from "@/shared/lib/labels";
import type { CorrectionRequest, Meta, TicketDetail } from "../types";

// Radix Select does not allow an empty item value.
const ROUTED_TEAM = "routed";

type Props = {
  ticket: TicketDetail;
  meta: Meta;
  busy: boolean;
  onSubmit: (correction: CorrectionRequest) => void;
};

export function CorrectionForm({ ticket, meta, busy, onSubmit }: Props) {
  const [category, setCategory] = useState(ticket.category ?? "");
  const [priority, setPriority] = useState(ticket.priority ?? "");
  const [team, setTeam] = useState(ticket.team ?? "");
  const [reason, setReason] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit({ category, priority, team: team || null, reason: reason.trim() || null });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          <h2>Tuzatish</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="correction-category">Kategoriya</Label>
            <Select
              value={category}
              onValueChange={(value) => {
                setCategory(value);
                setTeam(meta.routing[value] ?? "");
              }}
              required
            >
              <SelectTrigger id="correction-category">
                <SelectValue placeholder="Tanlang" />
              </SelectTrigger>
              <SelectContent>
                {meta.categories.map((value) => (
                  <SelectItem key={value} value={value}>
                    {CATEGORY[value] ?? value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="correction-priority">Ustuvorlik</Label>
            <Select value={priority} onValueChange={setPriority} required>
              <SelectTrigger id="correction-priority">
                <SelectValue placeholder="Tanlang" />
              </SelectTrigger>
              <SelectContent>
                {meta.priorities.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="correction-team">Jamoa</Label>
            <Select
              value={team || ROUTED_TEAM}
              onValueChange={(value) => setTeam(value === ROUTED_TEAM ? "" : value)}
            >
              <SelectTrigger id="correction-team">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ROUTED_TEAM}>Kategoriya bo‘yicha</SelectItem>
                {meta.teams.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="correction-reason">Izoh (ixtiyoriy)</Label>
            <Textarea
              id="correction-reason"
              rows={2}
              maxLength={1000}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </div>

          <Button type="submit" className="w-full" disabled={busy || !category || !priority}>
            Saqlash
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
