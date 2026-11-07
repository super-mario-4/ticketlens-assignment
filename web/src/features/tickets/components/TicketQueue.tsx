import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { PageHeader } from "@/shared/components/PageHeader";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useMeta } from "../hooks/use-meta";
import { PAGE_SIZE, useTicketList } from "../hooks/use-ticket-list";
import { TicketFilters } from "./TicketFilters";
import { TicketList } from "./TicketList";
import { TicketPagination } from "./TicketPagination";

const SKELETON_ROWS = [0, 1, 2, 3, 4, 5];

export function TicketQueue({ title, review = false }: { title: string; review?: boolean }) {
  const { meta, error: metaError } = useMeta();
  const list = useTicketList(review);
  const error = list.error || metaError;

  return (
    <div className="space-y-4">
      <PageHeader title={title} />
      <TicketFilters
        meta={meta}
        review={review}
        filters={list.filters}
        filtered={list.filtered}
        onFilter={list.setFilter}
        onSearch={list.search}
        onClear={list.clear}
      />
      {error && <ErrorAlert message={error} />}

      <div className="space-y-4" aria-busy={list.loading}>
        {list.page && <TicketList tickets={list.page.items} review={review} />}
        {!list.page && list.loading && (
          <div className="space-y-2">
            {SKELETON_ROWS.map((row) => (
              <Skeleton key={row} className="h-14 w-full" />
            ))}
          </div>
        )}
        {list.page && list.page.total > 0 && (
          <TicketPagination page={list.page} pageSize={PAGE_SIZE} onOffset={list.setOffset} />
        )}
      </div>
    </div>
  );
}
