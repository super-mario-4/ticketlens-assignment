import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { CATEGORY } from "@/shared/lib/labels";
import type { TicketDetail } from "../types";
import { PriorityBadge } from "./PriorityBadge";

export function CurrentValuesCard({ ticket }: { ticket: TicketDetail }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          <h2>Amaldagi qiymat</h2>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <PriorityBadge priority={ticket.priority} />
        <p>{ticket.category ? (CATEGORY[ticket.category] ?? ticket.category) : "—"}</p>
        <p>{ticket.team ?? "Jamoasiz"}</p>
      </CardContent>
    </Card>
  );
}
