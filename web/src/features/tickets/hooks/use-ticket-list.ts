import { useCallback, useState } from "react";
import { useRequest } from "@/shared/hooks/use-request";
import { fetchTickets } from "../api/tickets";
import type { TicketFilterValues } from "../types";

export const PAGE_SIZE = 50;

const NO_FILTERS: TicketFilterValues = {
  category: "",
  priority: "",
  team: "",
  channel: "",
  status: "",
};

export function useTicketList(review: boolean) {
  const [filters, setFilters] = useState(NO_FILTERS);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);

  const load = useCallback(
    () =>
      fetchTickets({
        ...filters,
        status: review ? "needs_review" : filters.status,
        q: query,
        limit: PAGE_SIZE,
        offset,
      }),
    [filters, query, offset, review],
  );
  const { data: page, error, loading } = useRequest(load);

  function setFilter(name: keyof TicketFilterValues, value: string) {
    setFilters({ ...filters, [name]: value });
    setOffset(0);
  }

  function search(text: string) {
    setQuery(text.trim());
    setOffset(0);
  }

  function clear() {
    setFilters(NO_FILTERS);
    setQuery("");
    setOffset(0);
  }

  const filtered = query !== "" || Object.values(filters).some((value) => value !== "");

  return { page, error, loading, filters, filtered, offset, setOffset, setFilter, search, clear };
}
