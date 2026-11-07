import { request } from "@/shared/api/client";
import type {
  CorrectionRequest,
  Meta,
  TicketDetail,
  TicketPage,
  TicketQuery,
  TicketStatus,
} from "../types";

export function fetchMeta(): Promise<Meta> {
  return request<Meta>("/meta");
}

export function fetchTickets(query: TicketQuery): Promise<TicketPage> {
  const params = new URLSearchParams();
  for (const [name, value] of Object.entries(query)) {
    if (value !== "") params.set(name, String(value));
  }
  return request<TicketPage>(`/tickets?${params}`);
}

export function fetchTicket(id: string): Promise<TicketDetail> {
  return request<TicketDetail>(`/tickets/${id}`);
}

export function correctTicket(id: string, correction: CorrectionRequest): Promise<TicketDetail> {
  return request<TicketDetail>(`/tickets/${id}/classification`, {
    method: "PATCH",
    body: JSON.stringify(correction),
  });
}

export function reclassifyTicket(id: string): Promise<{ id: string; status: TicketStatus }> {
  return request(`/tickets/${id}/reclassify`, { method: "POST" });
}
