import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import type { TicketPage } from "../types";

type Props = { page: TicketPage; pageSize: number; onOffset: (offset: number) => void };

export function TicketPagination({ page, pageSize, onOffset }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
      <span className="tabular-nums">
        {page.offset + 1}–{page.offset + page.items.length} / {page.total}
      </span>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="bg-card"
          disabled={page.offset === 0}
          onClick={() => onOffset(page.offset - pageSize)}
        >
          <ChevronLeft aria-hidden />
          Oldingi
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="bg-card"
          disabled={page.offset + pageSize >= page.total}
          onClick={() => onOffset(page.offset + pageSize)}
        >
          Keyingi
          <ChevronRight aria-hidden />
        </Button>
      </div>
    </div>
  );
}
