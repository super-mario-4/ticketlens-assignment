import { Link, useLocation } from "react-router";
import { Card, CardContent } from "@/shared/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { dateText } from "@/shared/lib/format";
import { CATEGORY, STATUS } from "@/shared/lib/labels";
import { REVIEW_REASON } from "../labels";
import type { TicketItem } from "../types";
import { PriorityBadge } from "./PriorityBadge";

type Props = { tickets: TicketItem[]; review: boolean };

function ticketTitle(ticket: TicketItem): string {
  return ticket.summary ?? ticket.preview ?? "Matn yo‘q";
}

function classText(ticket: TicketItem, review: boolean): string {
  if (review) return ticket.review_reason ? REVIEW_REASON[ticket.review_reason] : "—";
  if (ticket.category) return CATEGORY[ticket.category] ?? ticket.category;
  return STATUS[ticket.status] ?? ticket.status;
}

export function TicketList({ tickets, review }: Props) {
  // Tells the ticket page which list to link back to.
  const from = useLocation().pathname;

  if (tickets.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-sm text-muted-foreground">
          Ticket topilmadi.
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <div className="hidden rounded-lg border bg-card md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Ustuvorlik</TableHead>
              <TableHead>Murojaat</TableHead>
              <TableHead>{review ? "Sabab" : "Kategoriya"}</TableHead>
              <TableHead>Jamoa</TableHead>
              <TableHead>Kelgan vaqti</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tickets.map((ticket) => (
              <TableRow key={ticket.id} className="align-top">
                <TableCell>
                  <PriorityBadge priority={ticket.priority} />
                </TableCell>
                <TableCell className="max-w-md">
                  <Link
                    to={`/tickets/${ticket.id}`}
                    state={{ from }}
                    className="font-medium underline-offset-4 hover:underline"
                  >
                    {ticketTitle(ticket)}
                  </Link>
                  <div className="text-xs text-muted-foreground">
                    {ticket.source_ticket_id} · {ticket.channel}
                  </div>
                </TableCell>
                <TableCell>{classText(ticket, review)}</TableCell>
                <TableCell>{ticket.team ?? "—"}</TableCell>
                <TableCell className="whitespace-nowrap text-muted-foreground">
                  {dateText(ticket.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <ul className="space-y-2 md:hidden">
        {tickets.map((ticket) => (
          <li key={ticket.id}>
            <Link
              to={`/tickets/${ticket.id}`}
              state={{ from }}
              className="block rounded-lg focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <Card>
                <CardContent className="space-y-2 p-4 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    <PriorityBadge priority={ticket.priority} />
                    <span className="text-xs text-muted-foreground">
                      {dateText(ticket.created_at)}
                    </span>
                  </div>
                  <p className="break-words font-medium">{ticketTitle(ticket)}</p>
                  <p className="text-muted-foreground">
                    {classText(ticket, review)} · {ticket.team ?? "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {ticket.source_ticket_id} · {ticket.channel}
                  </p>
                </CardContent>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
